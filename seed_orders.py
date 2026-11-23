import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import create_app, db
from app.models import User, MenuItem, Order, OrderItem

app = create_app()

DEMO_PREFIX = "demo"
DEMO_DOMAIN = "@example.com"
NAMES = ["Thabo", "Lerato", "Sipho", "Naledi", "Pieter", "Aisha", "Tshepo", "Zanele"]
PEAK_HOURS = [11, 12, 12, 13, 13, 14, 17, 18, 18, 19, 19, 20, 21]  # local time, weighted


def is_demo(user):
    return user.email.startswith(DEMO_PREFIX) and user.email.endswith(DEMO_DOMAIN)


def clear():
    users = [u for u in User.query.all() if is_demo(u)]
    for user in users:
        for order in list(user.orders):
            db.session.delete(order)
        db.session.delete(user)
    db.session.commit()
    print(f"Removed {len(users)} demo customers and their orders.")


def generate():
    if User.query.filter_by(email=f"{DEMO_PREFIX}1{DEMO_DOMAIN}").first():
        print("Demo data already exists. Run with --clear first to regenerate.")
        return
    items = MenuItem.query.filter_by(available=True).all()
    if not items:
        print("No menu items found. Run seed.py first.")
        return

    random.seed(42)
    customers = []
    for i, name in enumerate(NAMES, start=1):
        user = User(name=name, email=f"{DEMO_PREFIX}{i}{DEMO_DOMAIN}")
        user.set_password("demo-password")
        db.session.add(user)
        customers.append(user)
    db.session.flush()

    now = datetime.now(timezone.utc)
    count = 0
    for days_ago in range(60, 0, -1):
        day = now - timedelta(days=days_ago)
        busy = day.weekday() >= 4  # Fri, Sat, Sun
        for _ in range(random.randint(8, 16) if busy else random.randint(3, 9)):
            local_hour = random.choice(PEAK_HOURS)
            created = day.replace(
                hour=(local_hour - 2) % 24,  # local time -> UTC
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0,
                tzinfo=None,
            )
            is_delivery = random.random() < 0.4
            cancelled = random.random() < 0.05
            fee = Decimal("30.00") if is_delivery else Decimal("0")

            order = Order(
                user_id=random.choice(customers).id,
                order_type="delivery" if is_delivery else "pickup",
                status="Cancelled" if cancelled else ("Delivered" if is_delivery else "Completed"),
                phone="0710000000",
                delivery_address="12 Demo Street, Polokwane" if is_delivery else None,
                delivery_fee=fee,
                total=Decimal("0"),
                created_at=created,
            )
            subtotal = Decimal("0")
            for item in random.sample(items, k=min(len(items), random.randint(1, 4))):
                qty = random.randint(1, 3)
                order.items.append(
                    OrderItem(menu_item_id=item.id, quantity=qty, unit_price=item.price)
                )
                subtotal += item.price * qty
            order.total = subtotal + fee
            db.session.add(order)
            count += 1

    db.session.commit()
    print(f"Created {len(customers)} demo customers and {count} demo orders.")


with app.app_context():
    if "--clear" in sys.argv:
        clear()
    else:
        generate()