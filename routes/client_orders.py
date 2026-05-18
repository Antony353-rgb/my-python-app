from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database.db import query_db
from utils.decorators import login_required, role_required
from services.voucher_service import get_order_codes
from utils.export import export_csv

client_orders_bp = Blueprint("client_orders", __name__, url_prefix="/client/orders")

@client_orders_bp.route("/")
@login_required
@role_required("client")
def orders_list():
    client_id = session.get("client_id")
    order_type = request.args.get("order_type")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = """SELECT o.*, cu.code as currency_code, cu.symbol
           FROM orders o JOIN currencies cu ON cu.id=o.currency_id
           WHERE o.client_id=?"""
    args = [client_id]
    if order_type: q += " AND o.order_type=?"; args.append(order_type)
    if date_from: q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    q += " ORDER BY o.created_at DESC"
    orders = query_db(q, args)
    return render_template("client/orders_list.html", orders=orders,
                           filters={"order_type": order_type, "date_from": date_from, "date_to": date_to})

@client_orders_bp.route("/<int:order_id>")
@login_required
@role_required("client")
def order_detail(order_id):
    client_id = session.get("client_id")
    order = query_db("""SELECT o.*, cu.code as currency_code, cu.symbol
                        FROM orders o JOIN currencies cu ON cu.id=o.currency_id
                        WHERE o.id=? AND o.client_id=?""", (order_id, client_id), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("client_orders.orders_list"))
    items = query_db("""SELECT oi.*, p.name as product_name, d.label as denomination_label
                        FROM order_items oi JOIN products p ON p.id=oi.product_id
                        JOIN denominations d ON d.id=oi.denomination_id
                        WHERE oi.order_id=?""", (order_id,))
    item_codes = {}
    for item in items:
        if item["status"] == "delivered":
            item_codes[item["id"]] = get_order_codes(item["id"])
    return render_template("client/order_detail.html", order=order, items=items, item_codes=item_codes)

@client_orders_bp.route("/<int:order_id>/download-codes")
@login_required
@role_required("client")
def download_codes(order_id):
    client_id = session.get("client_id")
    order = query_db("SELECT * FROM orders WHERE id=? AND client_id=? AND status='delivered'",
                     (order_id, client_id), one=True)
    if not order:
        flash("Order not available for download.", "danger")
        return redirect(url_for("client_orders.orders_list"))
    items = query_db("SELECT id FROM order_items WHERE order_id=?", (order_id,))
    all_codes = []
    for item in items:
        all_codes.extend(get_order_codes(item["id"]))
    headers = ["Code", "PIN", "Expiry"]
    data = [[c["code"], c["pin"] or "", c["expiry_date"] or ""] for c in all_codes]
    return export_csv(headers, data, filename=f"codes_{order['order_number']}.csv")
