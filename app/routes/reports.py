from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request
from sqlalchemy import text
from .. import db
from .admin import staff_required

reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")

# Timestamps are stored in UTC; South Africa is UTC+2, so shift before grouping.
LOCAL = "'+2 hours'"


@reports_bp.route("/")
@staff_required
def index():
    days = request.args.get("days", 30, type=int)
    if days not in (7, 30, 90):
        days = 30
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    params = {"since": since}

    summary = db.session.execute(text("""
        SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue
        FROM "order"
        WHERE status != 'Cancelled' AND created_at >= :since
    """), params).one()
    orders_count = summary.orders
    revenue = round(summary.revenue, 2)
    avg_order = round(revenue / orders_count, 2) if orders_count else 0

    daily = db.session.execute(text(f"""
        SELECT date(created_at, {LOCAL}) AS day,
               COUNT(*) AS orders,
               ROUND(SUM(total), 2) AS revenue
        FROM "order"
        WHERE status != 'Cancelled' AND created_at >= :since
        GROUP BY day
        ORDER BY day
    """), params).all()

    top_items = db.session.execute(text("""
        SELECT m.name AS name,
               SUM(oi.quantity) AS qty,
               ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_item oi
        JOIN "order" o ON o.id = oi.order_id
        JOIN menu_item m ON m.id = oi.menu_item_id
        WHERE o.status != 'Cancelled' AND o.created_at >= :since
        GROUP BY m.id
        ORDER BY qty DESC
        LIMIT 5
    """), params).all()

    by_hour_rows = db.session.execute(text(f"""
        SELECT CAST(strftime('%H', created_at, {LOCAL}) AS INTEGER) AS hour,
               COUNT(*) AS orders
        FROM "order"
        WHERE status != 'Cancelled' AND created_at >= :since
        GROUP BY hour
    """), params).all()
    by_hour = {r.hour: r.orders for r in by_hour_rows}

    by_type = db.session.execute(text("""
        SELECT order_type, COUNT(*) AS orders, ROUND(SUM(total), 2) AS revenue
        FROM "order"
        WHERE status != 'Cancelled' AND created_at >= :since
        GROUP BY order_type
    """), params).all()

    return render_template(
        "reports.html",
        days=days,
        orders_count=orders_count,
        revenue=revenue,
        avg_order=avg_order,
        daily_labels=[r.day for r in daily],
        daily_revenue=[r.revenue for r in daily],
        top_labels=[r.name for r in top_items],
        top_qty=[r.qty for r in top_items],
        hour_labels=[f"{h:02d}:00" for h in range(24)],
        hour_orders=[by_hour.get(h, 0) for h in range(24)],
        type_labels=[r.order_type.capitalize() for r in by_type],
        type_orders=[r.orders for r in by_type],
        top_items=top_items,
    )