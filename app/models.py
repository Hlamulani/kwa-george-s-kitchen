from . import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    items = db.relationship("MenuItem", backref="category", lazy=True)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300))
    price = db.Column(db.Numeric(8, 2), nullable=False)
    available = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)