from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"

    db.init_app(app)

    from .routes.menu import menu_bp
    app.register_blueprint(menu_bp)

    with app.app_context():
        db.create_all()

    return app