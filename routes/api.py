"""
Client-facing REST API for programmatic order placement.
Used by B2B clients who want to integrate directly.
"""
from flask import Blueprint, request, jsonify, session
from database.db import query_db
from services.order_service import create_order
from services.pricing_engine import get_best_supplier_rate, get_client_selling_price
from utils.decorators import login_required
from functools import wraps
import hashlib, time

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

def api_auth(f):
    """Simple API key authentication for programmatic access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not api_key:
            return jsonify({"error": "API key required", "code": 401}), 401
        user = query_db(
            "SELECT * FROM users WHERE totp_secret=? AND is_active=1 AND user_type='client'",
            (api_key,), one=True
        )
        if not user:
            return jsonify({"error": "Invalid API key", "code": 401}), 401
        request.api_user = user
        request.api_client_id = user["client_id"]
        return f(*args, **kwargs)
    return decorated

@api_bp.route("/ping")
def ping():
    return jsonify({"status": "ok", "timestamp": int(time.time())})

@api_bp.route("/balance")
@api_auth
def get_balance():
    client_id = request.api_client_id
    balances = query_db("""SELECT cu.code, cu.symbol, cfb.balance
                           FROM client_fund_balances cfb
                           JOIN currencies cu ON cu.id=cfb.currency_id
                           WHERE cfb.client_id=?""", (client_id,))
    return jsonify({
        "client_id": client_id,
        "balances": [{"currency": b["code"], "symbol": b["symbol"], "balance": b["balance"]} for b in balances]
    })

@api_bp.route("/search")
@api_auth
def search():
    client_id = request.api_client_id
    brand_id = request.args.get("brand_id")
    country_id = request.args.get("country_id")
    currency_id = request.args.get("currency_id")
    if not brand_id or not currency_id:
        return jsonify({"error": "brand_id and currency_id are required"}), 400
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    currency = query_db("SELECT * FROM currencies WHERE id=?", (currency_id,), one=True)
    if not currency:
        return jsonify({"error": "Currency not found"}), 404
    q = """SELECT DISTINCT p.id, p.name, d.id as denomination_id, d.label as denomination,
                  b.name as brand, co.name as country, cu.code as currency_code,
                  cp.client_rate_type, cp.client_rate_value, cp.min_markup_pct
           FROM client_catalogues cc
           JOIN catalogues cat ON cat.id=cc.catalogue_id
           JOIN catalogue_products cp ON cp.catalogue_id=cat.id AND cp.is_active=1
           JOIN products p ON p.id=cp.product_id AND p.is_active=1
           JOIN brands b ON b.id=p.brand_id
           JOIN countries co ON co.id=p.country_id
           JOIN currencies cu ON cu.id=p.currency_id
           JOIN denominations d ON d.id=cp.denomination_id
           WHERE cc.client_id=? AND b.id=?"""
    args = [client_id, brand_id]
    if country_id:
        q += " AND co.id=?"; args.append(country_id)
    products = query_db(q, args)
    results = []
    for p in products:
        rates = get_best_supplier_rate(p["id"], p["denomination_id"], currency["code"], client["fx_buffer_pct"])
        if rates:
            best = rates[0]
            cat_prod = {"client_rate_type": p["client_rate_type"], "client_rate_value": p["client_rate_value"]}
            selling = get_client_selling_price(best["cost_price_converted"], cat_prod, p["min_markup_pct"])
            results.append({
                "product_id": p["id"],
                "product_name": p["name"],
                "brand": p["brand"],
                "country": p["country"],
                "denomination_id": p["denomination_id"],
                "denomination": p["denomination"],
                "currency": currency["code"],
                "selling_price": selling,
                "stock": best["stock_count"],
                "in_stock": best["stock_count"] > 0
            })
    return jsonify({"results": results, "count": len(results)})

@api_bp.route("/order", methods=["POST"])
@api_auth
def place_order():
    client_id = request.api_client_id
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    items_data = data.get("items", [])
    currency_id = data.get("currency_id")
    if not items_data or not currency_id:
        return jsonify({"error": "items and currency_id required"}), 400
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    currency = query_db("SELECT * FROM currencies WHERE id=?", (currency_id,), one=True)
    if not currency:
        return jsonify({"error": "Currency not found"}), 404
    items = []
    for i in items_data:
        product_id = i.get("product_id")
        denomination_id = i.get("denomination_id")
        qty = i.get("qty", 1)
        rates = get_best_supplier_rate(product_id, denomination_id, currency["code"], client["fx_buffer_pct"])
        if not rates:
            return jsonify({"error": f"No rate available for product {product_id}"}), 400
        best = rates[0]
        cat_prod_row = query_db("""SELECT cp.* FROM client_catalogues cc
                                   JOIN catalogue_products cp ON cp.catalogue_id=cc.catalogue_id
                                   WHERE cc.client_id=? AND cp.product_id=? AND cp.denomination_id=? AND cp.is_active=1
                                   LIMIT 1""", (client_id, product_id, denomination_id), one=True)
        if not cat_prod_row:
            return jsonify({"error": f"Product {product_id} not in your catalogue"}), 403
        cat_prod = {"client_rate_type": cat_prod_row["client_rate_type"], "client_rate_value": cat_prod_row["client_rate_value"]}
        selling = get_client_selling_price(best["cost_price_converted"], cat_prod, cat_prod_row["min_markup_pct"])
        items.append({
            "product_id": product_id, "denomination_id": denomination_id,
            "supplier_id": best["supplier_id"], "supplier_rate_id": best["supplier_rate_id"],
            "qty": qty, "cost_price": best["cost_price_converted"], "selling_price": selling
        })
    order_id, err = create_order(client_id, currency_id, "api", items, request.api_user["id"])
    if err:
        return jsonify({"error": err}), 400
    order = query_db("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
    return jsonify({
        "success": True,
        "order_id": order_id,
        "order_number": order["order_number"],
        "invoice_number": order["invoice_number"],
        "total": order["total_amount"],
        "currency": currency["code"],
        "status": order["status"]
    }), 201

@api_bp.route("/order/<int:order_id>")
@api_auth
def order_status(order_id):
    client_id = request.api_client_id
    order = query_db("""SELECT o.*, cu.code as currency_code FROM orders o
                        JOIN currencies cu ON cu.id=o.currency_id
                        WHERE o.id=? AND o.client_id=?""", (order_id, client_id), one=True)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    items = query_db("""SELECT oi.*, p.name as product_name, d.label as denomination,
                               vc.code as voucher_code, vc.pin
                        FROM order_items oi
                        JOIN products p ON p.id=oi.product_id
                        JOIN denominations d ON d.id=oi.denomination_id
                        LEFT JOIN voucher_codes vc ON vc.order_item_id=oi.id AND vc.status='sold'
                        WHERE oi.order_id=?""", (order_id,))
    return jsonify({
        "order_number": order["order_number"],
        "status": order["status"],
        "total": order["total_amount"],
        "currency": order["currency_code"],
        "items": [dict(i) for i in items]
    })

@api_bp.route("/orders")
@api_auth
def order_list():
    client_id = request.api_client_id
    orders = query_db("""SELECT o.order_number, o.status, o.total_amount, o.order_type,
                                cu.code as currency_code, o.created_at
                         FROM orders o JOIN currencies cu ON cu.id=o.currency_id
                         WHERE o.client_id=? ORDER BY o.created_at DESC LIMIT 50""", (client_id,))
    return jsonify({"orders": [dict(o) for o in orders]})
