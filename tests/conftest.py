from decimal import Decimal

import pytest

from app import create_app, db
from app.models import User, Category, MenuItem
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    """Create a user in the test database and return their id."""
    def _make(email, role="customer", name="Test User"):
        with app.app_context():
            user = User(name=name, email=email, role=role)
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            return user.id
    return _make


@pytest.fixture
def login():
    """Log a given test client in as a given user."""
    def _login(client, email):
        return client.post(
            "/login", data={"email": email, "password": "password123"}
        )
    return _login


@pytest.fixture
def menu(app):
    """Two menu items, returned as {'burger': id, 'curry': id}."""
    with app.app_context():
        category = Category(name="Mains")
        db.session.add(category)
        db.session.flush()
        burger = MenuItem(name="Burger", description="", price=Decimal("95.00"),
                          category_id=category.id)
        curry = MenuItem(name="Curry", description="", price=Decimal("85.00"),
                         category_id=category.id)
        db.session.add_all([burger, curry])
        db.session.commit()
        return {"burger": burger.id, "curry": curry.id}