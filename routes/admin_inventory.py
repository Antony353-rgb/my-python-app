from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from services.inventory_service import create_inventory_order, record_inventory_delivery, get_inventory_balance
from datetime import datetime
import csv, io

inventory_bp = Blueprint("inventory", __name__, url_prefix="/admin/inventory")

@inventory_bp.route("/")
@login_required
@role_required("superadmin", "internal")
def inventory_list():
    orders = query_db("""
        SELECT io.*, s.name as supplier_name, p.name as product_name, d.label as denomination_label
        FROM inventory_orders io
        JOIN suppliers s ON s.id=io.supplier_id
        JOIN products p ON p.id=io.product_id
        JOIN denominations d ON d.id=io.denomination_id
        ORDER BY io.created_at DESC
    """)
    balance = get_inventory_balance()
    return render_template("admin/inventory_list.html", orders=orders, balance=balance)

@inventory_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("superadmin", "internal")
def inventory_create():
    if request.method == "POST":
        supplier_id = request.form.get("supplier_id")
        product_id = request.form.get("product_id")
        denomination_id = request.form.get("denomination_id")
        qty = int(request.form.get("qty", 0))
        cost_price = float(request.form.get("cost_price", 0))
        lpo_number = request.form.get("lpo_number", "").strip()
        remarks = request.form.get("remarks", "").strip()
        if not all([supplier_id, product_id, denomination_id, qty, cost_price]):
            flash("All fields required.", "danger")
            return redirect(url_for("inventory.inventory_create"))
        from flask import session
        inv_id = create_inventory_order(supplier_id, product_id, denomination_id, qty, cost_price,
                                        lpo_number=lpo_number, remarks=remarks,
                                        created_by=session.get("user_id"))
        log_action("create", "inventory", inv_id)
        flash("Inventory order created.", "success")
        return redirect(url_for("inventory.inventory_list"))
    suppliers = query_db("SELECT * FROM suppliers WHERE is_active=1 ORDER BY name")
    products = query_db("SELECT p.*, b.name as brand_name FROM products p JOIN brands b ON b.id=p.brand_id WHERE p.is_active=1 ORDER BY b.name, p.name")
    denominations = query_db("SELECT * FROM denominations WHERE is_active=1")
    return render_template("admin/inventory_create.html", suppliers=suppliers, products=products, denominations=denominations)

@inventory_bp.route("/<int:inv_id>/deliver", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def record_delivery(inv_id):
    qty = int(request.form.get("qty_delivered", 0))
    codes_raw = request.form.get("codes", "").strip()
    codes = []
    if codes_raw:
        for line in codes_raw.splitlines():
            parts = line.strip().split(",")
            if parts[0].strip():
                codes.append({"code": parts[0].strip(), "pin": parts[1].strip() if len(parts) > 1 else None})
    ok, msg = record_inventory_delivery(inv_id, qty, codes)
    flash(msg, "success" if ok else "danger")
    log_action("delivery", "inventory", inv_id)
    return redirect(url_for("inventory.inventory_list"))
