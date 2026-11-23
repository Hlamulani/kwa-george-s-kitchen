from functools import wraps
from decimal import Decimal, InvalidOperation
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user
from .. import db
from ..models import Order, MenuItem, Category

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

FLOW = {
    "pickup": ["Placed", "Confirmed", "Preparing", "Ready for pickup", "Completed"],
    "delivery": ["Placed", "Confirmed", "Preparing", "Out for delivery", "Delivered"],
}
FINAL = {"Completed", "Delivered", "Cancelled"}


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.role != "staff":
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapped)


def next_status(order):
    if order.status in FINAL:
        return None
    flow = FLOW[order.order_type]
    index = flow.index(order.status)
    return flow[index + 1] if index + 1 < len(flow) else None


# ---------- Orders ----------

@admin_bp.route("/")
@staff_required
def orders():
    status = request.args.get("status", "active")
    query = Order.query
    if status == "active":
        query = query.filter(~Order.status.in_(FINAL))
    elif status != "all":
        query = query.filter_by(status=status)
    rows = [(o, next_status(o)) for o in query.order_by(Order.created_at.asc()).all()]
    all_statuses = ["Placed", "Confirmed", "Preparing", "Ready for pickup",
                    "Out for delivery", "Completed", "Delivered", "Cancelled"]
    return render_template(
        "admin_orders.html", rows=rows, current=status, all_statuses=all_statuses
    )


@admin_bp.route("/orders/<int:order_id>/advance", methods=["POST"])
@staff_required
def advance(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    new_status = next_status(order)
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} is now: {new_status}.", "success")
    return redirect(request.referrer or url_for("admin.orders"))


@admin_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@staff_required
def cancel(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    if order.status not in FINAL:
        order.status = "Cancelled"
        db.session.commit()
        flash(f"Order #{order.id} cancelled.", "warning")
    return redirect(request.referrer or url_for("admin.orders"))


# ---------- Menu management ----------

@admin_bp.route("/menu")
@staff_required
def menu():
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin_menu.html", categories=categories)


@admin_bp.route("/categories/new", methods=["POST"])
@staff_required
def new_category():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Enter a category name.", "danger")
    elif Category.query.filter_by(name=name).first():
        flash("That category already exists.", "danger")
    else:
        db.session.add(Category(name=name))
        db.session.commit()
        flash(f"Category '{name}' added.", "success")
    return redirect(url_for("admin.menu"))


@admin_bp.route("/menu/<int:item_id>/toggle", methods=["POST"])
@staff_required
def toggle(item_id):
    item = db.session.get(MenuItem, item_id) or abort(404)
    item.available = not item.available
    db.session.commit()
    return redirect(url_for("admin.menu"))


def save_item(item):
    """Read the form into an item. Returns True if valid."""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category_id = request.form.get("category_id", type=int)
    try:
        price = Decimal(request.form.get("price", ""))
        if price < 0:
            raise InvalidOperation
    except InvalidOperation:
        flash("Enter a valid price.", "danger")
        return False
    if not name or not category_id:
        flash("Name and category are required.", "danger")
        return False
    item.name = name
    item.description = description
    item.price = price
    item.category_id = category_id
    item.available = "available" in request.form
    return True


@admin_bp.route("/menu/new", methods=["GET", "POST"])
@staff_required
def new_item():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        item = MenuItem()
        if save_item(item):
            db.session.add(item)
            db.session.commit()
            flash(f"'{item.name}' added to the menu.", "success")
            return redirect(url_for("admin.menu"))
    return render_template("item_form.html", item=None, categories=categories)


@admin_bp.route("/menu/<int:item_id>/edit", methods=["GET", "POST"])
@staff_required
def edit_item(item_id):
    item = db.session.get(MenuItem, item_id) or abort(404)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        if save_item(item):
            db.session.commit()
            flash(f"'{item.name}' updated.", "success")
            return redirect(url_for("admin.menu"))
    return render_template("item_form.html", item=item, categories=categories)