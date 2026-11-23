import os


class Config:
    # In production, set SECRET_KEY as an environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///restaurant.db")