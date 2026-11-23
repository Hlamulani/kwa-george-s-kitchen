from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .. import db
from ..models import Delivery
from .admin import FINAL, next_status, set_status

driver_bp = Blueprint("driver", __name__, url_prefix="/driver")


def driver_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.role != "driver":
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapped)


@driver_bp.route("/")
@driver_required
def deliveries():
    mine = (
        Delivery.query.filter_by(driver_id=current_user.id)
        .order_by(Delivery.assigned_at.desc())
        .all()
    )
    active = [d for d in mine if d.order.status not in FINAL]
    done = [d for d in mine if d.order.status in FINAL]
    return render_template("driver.html", active=active, done=done[:10])


@driver_bp.route("/<int:delivery_id>/advance", methods=["POST"])
@driver_required
def advance(delivery_id):
    delivery = db.session.get(Delivery, delivery_id) or abort(404)
    if delivery.driver_id != current_user.id:
        abort(404)
    order = delivery.order
    if order.status not in ("Preparing", "Out for delivery"):
        flash("This order isn't ready for you yet.", "warning")
    else:
        new_status = next_status(order)
        set_status(order, new_status)
        db.session.commit()
        flash(f"Order #{order.id} is now: {new_status}.", "success")
    return redirect(url_for("driver.deliveries"))