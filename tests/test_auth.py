from app.models import User


def register(client, email="new@example.com", password="secret123"):
    return client.post("/register", data={
        "name": "New User", "email": email, "password": password,
    })


def test_register_creates_customer_with_hashed_password(app, client):
    register(client)

    with app.app_context():
        user = User.query.filter_by(email="new@example.com").one()
        assert user.role == "customer"
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")


def test_duplicate_email_is_rejected(app, client):
    register(client)
    other = app.test_client()
    register(other)

    with app.app_context():
        assert User.query.filter_by(email="new@example.com").count() == 1


def test_short_password_is_rejected(app, client):
    register(client, password="123")

    with app.app_context():
        assert User.query.count() == 0


def test_wrong_password_does_not_log_in(client, make_user):
    make_user("c@example.com")

    client.post("/login", data={"email": "c@example.com", "password": "wrong"})

    assert client.get("/orders").status_code == 302  # still redirected to login


def test_correct_password_logs_in(client, make_user):
    make_user("c@example.com")

    client.post("/login", data={"email": "c@example.com", "password": "password123"})

    assert client.get("/orders").status_code == 200