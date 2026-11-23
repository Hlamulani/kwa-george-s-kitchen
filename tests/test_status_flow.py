from decimal import Decimal
from types import SimpleNamespace

import pytest

from app import db
from app.models import Order, OrderItem, Delivery
from app.routes.admin import next_status


def fake_order(status, order_type):
    return SimpleNamespace(status=status, order_type=order_type)


def walk(order_type):
    order = fake_order("Placed", order_type)
    steps = []
    while True:
        nxt = next_status(order)
        if not nxt:
            return steps
        steps.append(nxt)
        order.status = nxt


def test_pickup_flow():
    assert walk("pickup") == ["Confirmed", "Preparing", "Ready for pickup", "Completed"]


def test_delivery_flow():
    assert walk("delivery") == ["Confirmed", "Preparing", "Out for delivery", "Delivered"]


@pytest.mark.parametrize("status", ["Completed", "Delivered", "Cancelled"])
def test_finished_orders_have_no_next_status(status):
    assert next_status(fake_order(status, "delivery")) is None


def make_delivery_order(app, customer_id, menu, status="Preparing"):
    with app.app_context():
        order = Order(
            user_id=customer_id, order_type="delivery", status=status,
            phone="0710000000", delivery_address="1 Test Street",
            delivery_fee=Decimal("30.00"), total=Decimal("125.00"),
        )
        order.items.append(OrderItem(
            menu_item_id=menu["burger"], quantity=1, unit_price=Decimal("95.00")
        ))
        db.session.add(order)
        db.session.commit()
        return order.id


def test_cannot_send_out_without_driver(app, client, make_user, login, menu):
    customer = make_user("c@example.com")
    make_user("staff@example.com", role="staff")
    order_id = make_delivery_order(app, customer, menu)
    login(client, "staff@example.com")

    client.post(f"/admin/orders/{order_id}/advance")

    with app.app_context():
        assert db.session.get(Order, order_id).status == "Preparing"


def test_staff_can_assign_driver_then_send_out(app, client, make_user, login, menu):
    customer = make_user("c@example.com")
    make_user("staff@example.com", role="staff")
    driver = make_user("d@example.com", role="driver")
    order_id = make_delivery_order(app, customer, menu)
    login(client, "staff@example.com")

    client.post(f"/admin/orders/{order_id}/assign", data={"driver_id": driver})
    client.post(f"/admin/orders/{order_id}/advance")

    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "Out for delivery"
        assert order.delivery.driver_id == driver
        assert order.delivery.picked_up_at is not None


def test_cancelled_order_cannot_be_advanced(app, client, make_user, login, menu):
    customer = make_user("c@example.com")
    make_user("staff@example.com", role="staff")
    order_id = make_delivery_order(app, customer, menu, status="Placed")
    login(client, "staff@example.com")

    client.post(f"/admin/orders/{order_id}/cancel")
    client.post(f"/admin/orders/{order_id}/advance")

    with app.app_context():
        assert db.session.get(Order, order_id).status == "Cancelled"


def test_driver_can_mark_own_delivery_delivered(app, client, make_user, login, menu):
    customer = make_user("c@example.com")
    driver = make_user("d@example.com", role="driver")
    order_id = make_delivery_order(app, customer, menu, status="Out for delivery")
    with app.app_context():
        delivery = Delivery(order_id=order_id, driver_id=driver)
        db.session.add(delivery)
        db.session.commit()
        delivery_id = delivery.id
    login(client, "d@example.com")

    client.post(f"/driver/{delivery_id}/advance")

    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "Delivered"
        assert order.delivery.delivered_at is not None


def test_driver_cannot_touch_another_drivers_delivery(app, client, make_user, login, menu):
    customer = make_user("c@example.com")
    owner = make_user("d1@example.com", role="driver")
    make_user("d2@example.com", role="driver")
    order_id = make_delivery_order(app, customer, menu, status="Out for delivery")
    with app.app_context():
        delivery = Delivery(order_id=order_id, driver_id=owner)
        db.session.add(delivery)
        db.session.commit()
        delivery_id = delivery.id
    login(client, "d2@example.com")

    response = client.post(f"/driver/{delivery_id}/advance")

    assert response.status_code == 404
    with app.app_context():
        assert db.session.get(Order, order_id).status == "Out for delivery"