from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from utils.export import export_csv
from services.order_service import cancel_order
from services.voucher_service import get_order_codes
from services.notification_service import notify_order_delivered
from datetime import datetime
import csv, io

orders_admin_bp = Blueprint("orders_admin", __name__, url_prefix="/admin/orders")

@orders_admin_bp.route("/")
@login_required
@role_required("superadmin", "internal")
def orders_list():
    client_id = request.args.get("client_id")
    status = request.args.get("status")
    order_type = request.args.get("order_type")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = """SELECT o.*, c.name as client_name, cu.code as currency_code
           FROM orders o JOIN clients c ON c.id=o.client_id JOIN currencies cu ON cu.id=o.currency_id
           WHERE 1=1"""
    args = []
    if client_id: q += " AND o.client_id=?"; args.append(client_id)
    if status: q += " AND o.status=?"; args.append(status)
    if order_type: q += " AND o.order_type=?"; args.append(order_type)
    if date_from: q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    q += " ORDER BY o.created_at DESC LIMIT 200"
    orders = query_db(q, args)
    clients = query_db("SELECT id, name FROM clients WHERE is_active=1 ORDER BY name")
    return render_template("admin/orders_list.html", orders=orders, clients=clients,
                           filters={"client_id": client_id, "status": status,
                                    "order_type": order_type, "date_from": date_from, "date_to": date_to})

@orders_admin_bp.route("/<int:order_id>")
@login_required
@role_required("superadmin", "internal")
def order_detail(order_id):
    order = query_db("""SELECT o.*, c.name as client_name, cu.code as currency_code, cu.symbol
                        FROM orders o JOIN clients c ON c.id=o.client_id JOIN currencies cu ON cu.id=o.currency_id
                        WHERE o.id=?""", (order_id,), one=True)
    items = query_db("""SELECT oi.*, p.name as product_name, d.label as denomination_label,
                               s.name as supplier_name
                        FROM order_items oi JOIN products p ON p.id=oi.product_id
                        JOIN denominations d ON d.id=oi.denomination_id JOIN suppliers s ON s.id=oi.supplier_id
                        WHERE oi.order_id=?""", (order_id,))
    item_codes = {}
    for item in items:
        item_codes[item["id"]] = get_order_codes(item["id"])
    return render_template("admin/order_detail.html", order=order, items=items, item_codes=item_codes)

@orders_admin_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
@role_required("superadmin")
def cancel(order_id):
    reason = request.form.get("reason", "Cancelled by admin")
    ok, msg = cancel_order(order_id, session.get("user_id"), reason)
    if ok:
        flash(msg, "success")
        log_action("cancel", "orders", order_id)
    else:
        flash(msg, "danger")
    return redirect(url_for("orders_admin.order_detail", order_id=order_id))

@orders_admin_bp.route("/<int:order_id>/deliver", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def mark_delivered(order_id):
    item_id = request.form.get("item_id")
    execute_db("UPDATE order_items SET status='delivered' WHERE id=?", (item_id,))
    # Check if all items delivered
    pending = query_db("SELECT COUNT(*) as c FROM order_items WHERE order_id=? AND status!='delivered'",
                       (order_id,), one=True)
    if pending["c"] == 0:
        execute_db("UPDATE orders SET status='delivered', updated_at=? WHERE id=?",
                   (datetime.utcnow(), order_id))
        notify_order_delivered(order_id)
        flash("Order marked as delivered.", "success")
    else:
        flash("Item marked as delivered.", "success")
    log_action("deliver", "orders", order_id)
    return redirect(url_for("orders_admin.order_detail", order_id=order_id))

@orders_admin_bp.route("/<int:order_id>/upload-codes", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def upload_codes(order_id):
    item_id = request.form.get("item_id")
    codes_text = request.form.get("codes", "").strip()
    if not codes_text:
        flash("No codes provided.", "danger")
        return redirect(url_for("orders_admin.order_detail", order_id=order_id))
    item = query_db("SELECT * FROM order_items WHERE id=?", (item_id,), one=True)
    lines = [l.strip() for l in codes_text.splitlines() if l.strip()]
    for line in lines:
        parts = line.split(",")
        code = parts[0].strip()
        pin = parts[1].strip() if len(parts) > 1 else None
        try:
            execute_db("""INSERT INTO voucher_codes (product_id, denomination_id, supplier_id, code, pin, status, order_item_id, sold_at)
                          VALUES (?,?,?,?,?,'sold',?,?)""",
                       (item["product_id"], item["denomination_id"], item["supplier_id"],
                        code, pin, item_id, datetime.utcnow()))
        except Exception:
            pass
    execute_db("UPDATE order_items SET status='delivered' WHERE id=?", (item_id,))
    flash(f"Uploaded {len(lines)} codes.", "success")
    log_action("upload_codes", "orders", order_id)
    return redirect(url_for("orders_admin.order_detail", order_id=order_id))

@orders_admin_bp.route("/<int:order_id>/download-codes")
@login_required
@role_required("superadmin", "internal")
def download_codes_admin(order_id):
    order = query_db("SELECT order_number FROM orders WHERE id=?", (order_id,), one=True)
    items = query_db("SELECT id FROM order_items WHERE order_id=?", (order_id,))
    all_codes = []
    for item in items:
        codes = get_order_codes(item["id"])
        all_codes.extend(codes)
    headers = ["Code", "PIN", "Expiry"]
    data = [[c["code"], c["pin"] or "", c["expiry_date"] or ""] for c in all_codes]
    return export_csv(headers, data, filename=f"codes_{order['order_number']}.csv")
