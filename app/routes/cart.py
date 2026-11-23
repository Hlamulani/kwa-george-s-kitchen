from decimal import Decimal
from flask import (
    Blueprint, session, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user
from .. import db
from ..models import MenuItem, Order, OrderItem

cart_bp = Blueprint("cart", __name__)

DELIVERY_FEE = Decimal("30.00")


def get_cart_lines():
    """Return (lines, subtotal) from the session cart."""
    cart = session.get("cart", {})
    lines = []
    subtotal = Decimal("0")
    for item_id, qty in cart.items():
        item = db.session.get(MenuItem, int(item_id))
        if item and item.available:
            line_total = item.price * qty
            lines.append({"item": item, "qty": qty, "line_total": line_total})
            subtotal += line_total
    return lines, subtotal


@cart_bp.route("/cart")
def view_cart():
    lines, subtotal = get_cart_lines()
    return render_template("cart.html", lines=lines, subtotal=subtotal)


@cart_bp.route("/cart/add/<int:item_id>", methods=["POST"])
def add(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item or not item.available:
        abort(404)
    cart = dict(session.get("cart", {}))
    cart[str(item_id)] = cart.get(str(item_id), 0) + 1
    session["cart"] = cart
    flash(f"{item.name} added to your cart.", "success")
    return redirect(url_for("menu.index"))


@cart_bp.route("/cart/update/<int:item_id>", methods=["POST"])
def update(item_id):
    cart = dict(session.get("cart", {}))
    try:
        qty = int(request.form.get("quantity", 1))
    except ValueError:
        qty = 1
    if qty <= 0:
        cart.pop(str(item_id), None)
    elif str(item_id) in cart:
        cart[str(item_id)] = min(qty, 20)
    session["cart"] = cart
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove(item_id):
    cart = dict(session.get("cart", {}))
    cart.pop(str(item_id), None)
    session["cart"] = cart
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    lines, subtotal = get_cart_lines()
    if not lines:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("menu.index"))

    if request.method == "POST":
        order_type = request.form.get("order_type")
        phone = request.form.get("phone", "").strip()
        address = request.form.get("delivery_address", "").strip()

        if order_type not in ("pickup", "delivery") or not phone:
            flash("Choose pickup or delivery and enter a phone number.", "danger")
        elif order_type == "delivery" and not address:
            flash("Enter a delivery address.", "danger")
        else:
            fee = DELIVERY_FEE if order_type == "delivery" else Decimal("0")
            order = Order(
                user_id=current_user.id,
                order_type=order_type,
                phone=phone,
                delivery_address=address if order_type == "delivery" else None,
                delivery_fee=fee,
                total=subtotal + fee,
            )
            for line in lines:
                order.items.append(
                    OrderItem(
                        menu_item_id=line["item"].id,
                        quantity=line["qty"],
                        unit_price=line["item"].price,
                    )
                )
            db.session.add(order)
            db.session.commit()
            session.pop("cart", None)
            flash("Order placed! Thank you.", "success")
            return redirect(url_for("cart.order_detail", order_id=order.id))

    return render_template(
        "checkout.html", lines=lines, subtotal=subtotal, delivery_fee=DELIVERY_FEE
    )


@cart_bp.route("/orders")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders.html", orders=orders)


@cart_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order or (order.user_id != current_user.id and current_user.role != "staff"):
        abort(404)
    return render_template("order_detail.html", order=order)