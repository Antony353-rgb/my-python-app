from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from datetime import datetime

supplier_bp = Blueprint("supplier", __name__, url_prefix="/supplier")

@supplier_bp.route("/dashboard")
@login_required
@role_required("supplier")
def dashboard():
    supplier_id = session.get("supplier_id")
    stats = {
        "available_codes": query_db("SELECT COUNT(*) as c FROM voucher_codes WHERE supplier_id=? AND status='available'",
                                    (supplier_id,), one=True)["c"],
        "sold_codes": query_db("SELECT COUNT(*) as c FROM voucher_codes WHERE supplier_id=? AND status='sold'",
                               (supplier_id,), one=True)["c"],
        "pending_deliveries": query_db("""SELECT COUNT(*) as c FROM order_items oi
                                          JOIN orders o ON o.id=oi.order_id
                                          WHERE oi.supplier_id=? AND oi.status='ordered'""", (supplier_id,), one=True)["c"],
    }
    recent_orders = query_db("""SELECT oi.*, o.order_number, o.created_at, p.name as product_name
                                FROM order_items oi JOIN orders o ON o.id=oi.order_id
                                JOIN products p ON p.id=oi.product_id
                                WHERE oi.supplier_id=? ORDER BY o.created_at DESC LIMIT 10""", (supplier_id,))
    return render_template("supplier/dashboard.html", stats=stats, recent_orders=recent_orders)

@supplier_bp.route("/inventory")
@login_required
@role_required("supplier")
def inventory():
    supplier_id = session.get("supplier_id")
    codes = query_db("""SELECT vc.*, p.name as product_name, d.label as denomination_label
                        FROM voucher_codes vc JOIN products p ON p.id=vc.product_id
                        JOIN denominations d ON d.id=vc.denomination_id
                        WHERE vc.supplier_id=? ORDER BY vc.status, vc.uploaded_at DESC LIMIT 500""",
                     (supplier_id,))
    return render_template("supplier/inventory_list.html", codes=codes)

@supplier_bp.route("/orders")
@login_required
@role_required("supplier")
def orders():
    supplier_id = session.get("supplier_id")
    items = query_db("""SELECT oi.*, o.order_number, o.created_at, o.client_id,
                               p.name as product_name, d.label as denomination_label
                        FROM order_items oi JOIN orders o ON o.id=oi.order_id
                        JOIN products p ON p.id=oi.product_id JOIN denominations d ON d.id=oi.denomination_id
                        WHERE oi.supplier_id=? ORDER BY o.created_at DESC""", (supplier_id,))
    return render_template("supplier/orders_list.html", items=items)
