import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from . import db
from .models import User, Category, MenuItem, Order, OrderItem

PASSWORD = "demo1234"

MENU = {
    "Starters": [
        ("Spring Rolls", "Crispy vegetable rolls with sweet chilli dip", "45.00"),
        ("Chicken Wings", "Six wings with peri-peri glaze", "75.00"),
    ],
    "Mains": [
        ("Beef Burger", "Beef patty, cheddar, and chips", "95.00"),
        ("Grilled Chicken", "Half chicken with pap and chakalaka", "110.00"),
        ("Veggie Curry", "Chickpea and spinach curry with rice", "85.00"),
    ],
    "Drinks": [
        ("Soft Drink", "330ml can", "20.00"),
        ("Fresh Juice", "Orange or apple", "30.00"),
    ],
}

ACCOUNTS = [
    ("Demo Staff", "staff@demo.com", "staff"),
    ("Demo Driver", "driver@demo.com", "driver"),
    ("Demo Customer", "customer@demo.com", "customer"),
    ("Thabo", "thabo@demo.com", "customer"),
    ("Lerato", "lerato@demo.com", "customer"),
]

PEAK_HOURS = [11, 12, 12, 13, 13, 14, 17, 18, 18, 19, 19, 20, 21]  # local time


def seed_demo():
    """Fill an empty database with demo data. Does nothing if users exist."""
    if User.query.first():
        return

    items = []
    for category_name, rows in MENU.items():
        category = Category(name=category_name)
        db.session.add(category)
        for name, description, price in rows:
            item = MenuItem(name=name, description=description, price=Decimal(price))
            category.items.append(item)
            items.append(item)

    users = []
    for name, email, role in ACCOUNTS:
        user = User(name=name, email=email, role=role)
        user.set_password(PASSWORD)
        db.session.add(user)
        users.append(user)
    db.session.flush()

    customers = [u for u in users if u.role == "customer"]
    rng = random.Random(42)
    now = datetime.now(timezone.utc)

    for days_ago in range(30, 0, -1):
        day = now - timedelta(days=days_ago)
        busy = day.weekday() >= 4  # Fri, Sat, Sun
        for _ in range(rng.randint(6, 12) if busy else rng.randint(2, 6)):
            local_hour = rng.choice(PEAK_HOURS)
            created = day.replace(
                hour=(local_hour - 2) % 24,  # South Africa is UTC+2
                minute=rng.randint(0, 59), second=rng.randint(0, 59),
                microsecond=0, tzinfo=None,
            )
            is_delivery = rng.random() < 0.4
            cancelled = rng.random() < 0.05
            fee = Decimal("30.00") if is_delivery else Decimal("0")

            order = Order(
                user_id=rng.choice(customers).id,
                order_type="delivery" if is_delivery else "pickup",
                status="Cancelled" if cancelled else ("Delivered" if is_delivery else "Completed"),
                phone="0710000000",
                delivery_address="12 Demo Street, Polokwane" if is_delivery else None,
                delivery_fee=fee, total=Decimal("0"), created_at=created,
            )
            subtotal = Decimal("0")
            for item in rng.sample(items, k=rng.randint(1, 4)):
                qty = rng.randint(1, 3)
                order.items.append(
                    OrderItem(menu_item_id=item.id, quantity=qty, unit_price=item.price)
                )
                subtotal += item.price * qty
            order.total = subtotal + fee
            db.session.add(order)

    db.session.commit()