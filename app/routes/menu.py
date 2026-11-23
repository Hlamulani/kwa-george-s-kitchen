from flask import Blueprint, render_template
from ..models import Category

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/")
def index():
    categories = Category.query.all()
    return render_template("menu.html", categories=categories)