from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="customer")  # customer / staff / driver

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    items = db.relationship("MenuItem", backref="category", lazy=True)


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300))
    price = db.Column(db.Numeric(8, 2), nullable=False)
    available = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # pickup / delivery
    status = db.Column(db.String(30), default="Placed")
    phone = db.Column(db.String(30), nullable=False)
    delivery_address = db.Column(db.String(255))
    delivery_fee = db.Column(db.Numeric(8, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="orders")
    items = db.relationship(
        "OrderItem", backref="order", cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(8, 2), nullable=False)  # price at time of order

    menu_item = db.relationship("MenuItem")


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), unique=True, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    picked_up_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    order = db.relationship("Order", backref=db.backref("delivery", uselist=False))
    driver = db.relationship("User", backref="deliveries")