from decimal import Decimal

from app import db
from app.models import Order, OrderItem


def make_order(app, customer_id, menu):
    with app.app_context():
        order = Order(
            user_id=customer_id, order_type="pickup", phone="0710000000",
            total=Decimal("95.00"),
        )
        order.items.append(OrderItem(
            menu_item_id=menu["burger"], quantity=1, unit_price=Decimal("95.00")
        ))
        db.session.add(order)
        db.session.commit()
        return order.id


def test_anonymous_user_is_sent_to_login(client):
    for url in ["/admin/", "/admin/reports/", "/driver/", "/orders", "/checkout"]:
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_customer_cannot_open_staff_pages(client, make_user, login):
    make_user("c@example.com")
    login(client, "c@example.com")

    for url in ["/admin/", "/admin/menu", "/admin/reports/"]:
        assert client.get(url).status_code == 403


def test_customer_cannot_open_driver_page(client, make_user, login):
    make_user("c@example.com")
    login(client, "c@example.com")

    assert client.get("/driver/").status_code == 403


def test_driver_cannot_open_staff_pages(client, make_user, login):
    make_user("d@example.com", role="driver")
    login(client, "d@example.com")

    assert client.get("/admin/").status_code == 403


def test_staff_can_open_staff_pages(client, make_user, login):
    make_user("s@example.com", role="staff")
    login(client, "s@example.com")

    for url in ["/admin/", "/admin/menu", "/admin/reports/"]:
        assert client.get(url).status_code == 200


def test_customer_cannot_view_someone_elses_order(app, make_user, login, menu):
    owner_id = make_user("owner@example.com")
    make_user("other@example.com")
    order_id = make_order(app, owner_id, menu)

    other = app.test_client()
    login(other, "other@example.com")

    assert other.get(f"/orders/{order_id}").status_code == 404


def test_owner_and_staff_can_view_an_order(app, make_user, login, menu):
    owner_id = make_user("owner@example.com")
    make_user("s@example.com", role="staff")
    order_id = make_order(app, owner_id, menu)

    owner = app.test_client()
    login(owner, "owner@example.com")
    staff = app.test_client()
    login(staff, "s@example.com")

    assert owner.get(f"/orders/{order_id}").status_code == 200
    assert staff.get(f"/orders/{order_id}").status_code == 200