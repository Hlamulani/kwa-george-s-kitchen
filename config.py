import os


class Config:
    # In production, set SECRET_KEY as an environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///restaurant.db")
    DEMO_MODE = os.environ.get("DEMO_MODE") == "1"


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    DEMO_MODE = False