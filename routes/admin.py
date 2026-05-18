from flask import Blueprint, render_template, session, redirect, url_for
from database.db import query_db
from utils.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
@role_required("superadmin", "internal")
def dashboard():
    stats = {
        "total_clients": query_db("SELECT COUNT(*) as c FROM clients WHERE is_active=1", one=True)["c"],
        "total_suppliers": query_db("SELECT COUNT(*) as c FROM suppliers WHERE is_active=1", one=True)["c"],
        "total_orders": query_db("SELECT COUNT(*) as c FROM orders", one=True)["c"],
        "pending_orders": query_db("SELECT COUNT(*) as c FROM orders WHERE status='ordered' OR status='pending_delivery'", one=True)["c"],
        "today_orders": query_db("SELECT COUNT(*) as c FROM orders WHERE DATE(created_at)=DATE('now')", one=True)["c"],
        "today_revenue": query_db("SELECT SUM(total_amount) as s FROM orders WHERE DATE(created_at)=DATE('now') AND status!='cancelled'", one=True)["s"] or 0,
        "available_vouchers": query_db("SELECT COUNT(*) as c FROM voucher_codes WHERE status='available'", one=True)["c"],
        "total_profit": query_db("SELECT SUM(profit) as s FROM order_items WHERE status='delivered'", one=True)["s"] or 0,
        "monthly_revenue": query_db("SELECT SUM(total_amount) as s FROM orders WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') AND status != 'cancelled'", one=True)["s"] or 0,
        "monthly_orders_finished": query_db("SELECT COUNT(*) as c FROM orders WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') AND status = 'delivered'", one=True)["c"],
    }
    recent_orders = query_db("""
        SELECT o.*, c.name as client_name, cu.code as currency_code
        FROM orders o JOIN clients c ON c.id=o.client_id JOIN currencies cu ON cu.id=o.currency_id
        ORDER BY o.created_at DESC LIMIT 10
    """)
    low_stock = query_db("""
        SELECT p.name, d.label, COUNT(*) as stock_count
        FROM voucher_codes vc
        JOIN products p ON p.id=vc.product_id
        JOIN denominations d ON d.id=vc.denomination_id
        WHERE vc.status='available'
        GROUP BY vc.product_id, vc.denomination_id
        HAVING stock_count < 10
        ORDER BY stock_count ASC LIMIT 10
    """)
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders, low_stock=low_stock)
