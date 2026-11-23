from app import create_app, db
from app.models import Category, MenuItem

app = create_app()

MENU = {
    "Starters": [
        ("Spring Rolls", "Crispy vegetable rolls with sweet chilli dip", 45.00),
        ("Chicken Wings", "Six wings with peri-peri glaze", 75.00),
    ],
    "Mains": [
        ("Beef Burger", "Beef patty, cheddar, and chips", 95.00),
        ("Grilled Chicken", "Half chicken with pap and chakalaka", 110.00),
        ("Veggie Curry", "Chickpea and spinach curry with rice", 85.00),
    ],
    "Drinks": [
        ("Soft Drink", "330ml can", 20.00),
        ("Fresh Juice", "Orange or apple", 30.00),
    ],
}

with app.app_context():
    db.drop_all()
    db.create_all()

    for category_name, items in MENU.items():
        category = Category(name=category_name)
        db.session.add(category)
        for name, description, price in items:
            category.items.append(
                MenuItem(name=name, description=description, price=price)
            )

    db.session.commit()
    print("Database seeded.")