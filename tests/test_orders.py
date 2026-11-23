from decimal import Decimal

from app import db
from app.models import Order, OrderItem, MenuItem


def place_order(client, item_ids, order_type="pickup", address=""):
    for item_id in item_ids:
        client.post(f"/cart/add/{item_id}")
    return client.post("/checkout", data={
        "order_type": order_type,
        "phone": "0710000000",
        "delivery_address": address,
    })


def test_pickup_order_total(app, client, make_user, login, menu):
    make_user("c@example.com")
    login(client, "c@example.com")

    place_order(client, [menu["burger"], menu["curry"]])

    with app.app_context():
        order = Order.query.one()
        assert order.total == Decimal("180.00")
        assert order.delivery_fee == 0
        assert order.status == "Placed"
        assert len(order.items) == 2


def test_delivery_order_adds_fee_and_quantities(app, client, make_user, login, menu):
    make_user("c@example.com")
    login(client, "c@example.com")

    # Burger added twice = quantity 2 (R190) + R30 delivery
    place_order(client, [menu["burger"], menu["burger"]],
                order_type="delivery", address="1 Test Street")

    with app.app_context():
        order = Order.query.one()
        assert order.items[0].quantity == 2
        assert order.delivery_fee == Decimal("30.00")
        assert order.total == Decimal("220.00")


def test_delivery_requires_address(app, client, make_user, login, menu):
    make_user("c@example.com")
    login(client, "c@example.com")

    place_order(client, [menu["burger"]], order_type="delivery", address="")

    with app.app_context():
        assert Order.query.count() == 0


def test_order_keeps_price_paid_if_menu_price_changes(app, client, make_user, login, menu):
    make_user("c@example.com")
    login(client, "c@example.com")
    place_order(client, [menu["burger"]])

    with app.app_context():
        item = db.session.get(MenuItem, menu["burger"])
        item.price = Decimal("120.00")
        db.session.commit()

        order_item = OrderItem.query.one()
        assert order_item.unit_price == Decimal("95.00")


def test_cannot_check_out_empty_cart(app, client, make_user, login):
    make_user("c@example.com")
    login(client, "c@example.com")

    response = client.post("/checkout", data={
        "order_type": "pickup", "phone": "0710000000",
    })

    assert response.status_code == 302
    with app.app_context():
        assert Order.query.count() == 0


def test_unavailable_item_cannot_be_added(app, client, menu):
    with app.app_context():
        item = db.session.get(MenuItem, menu["burger"])
        item.available = False
        db.session.commit()

    response = client.post(f"/cart/add/{menu['burger']}")

    assert response.status_code == 404