from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"

    db.init_app(app)
    login_manager.init_app(app)

    from .routes.menu import menu_bp
    from .routes.auth import auth_bp
    from .routes.cart import cart_bp
    from .routes.admin import admin_bp
    from .routes.driver import driver_bp
    app.register_blueprint(menu_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(driver_bp)

    @app.context_processor
    def inject_cart_count():
        return {"cart_count": sum(session.get("cart", {}).values())}

    with app.app_context():
        from . import models  # make sure all tables are registered
        db.create_all()

    return app