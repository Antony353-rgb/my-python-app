from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from services.pricing_engine import get_best_supplier_rate, get_client_selling_price, calculate_selling_price
from services.order_service import create_order
from services.notification_service import get_user_notifications, mark_all_read
from utils.export import export_xlsx
from datetime import datetime

client_bp = Blueprint("client", __name__, url_prefix="/client")

@client_bp.route("/dashboard")
@login_required
@role_required("client")
def dashboard():
    client_id = session.get("client_id")
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    balances = query_db("""SELECT cfb.*, cu.code, cu.symbol, cu.name as currency_name
                           FROM client_fund_balances cfb JOIN currencies cu ON cu.id=cfb.currency_id
                           WHERE cfb.client_id=? ORDER BY cu.code""", (client_id,))
    recent_orders = query_db("""SELECT o.*, cu.code as currency_code
                                FROM orders o JOIN currencies cu ON cu.id=o.currency_id
                                WHERE o.client_id=? ORDER BY o.created_at DESC LIMIT 5""", (client_id,))
    unread_count = len(get_user_notifications(session.get("user_id"), unread_only=True))
    return render_template("client/dashboard.html", client=client, balances=balances,
                           recent_orders=recent_orders, unread_count=unread_count)

@client_bp.route("/search", methods=["GET", "POST"])
@login_required
@role_required("client")
def search():
    client_id = session.get("client_id")
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    currencies = query_db("""SELECT cu.* FROM client_currencies cc JOIN currencies cu ON cu.id=cc.currency_id
                             WHERE cc.client_id=? ORDER BY cc.is_default DESC, cu.code""", (client_id,))
    brands = query_db("SELECT DISTINCT b.* FROM brands b JOIN products p ON p.brand_id=b.id WHERE b.is_active=1 ORDER BY b.name")
    countries = query_db("SELECT * FROM countries WHERE is_active=1 ORDER BY name")
    return render_template("client/search.html", client=client, currencies=currencies,
                           brands=brands, countries=countries)

@client_bp.route("/search/results")
@login_required
@role_required("client")
def search_results():
    client_id = session.get("client_id")
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    brand_id = request.args.get("brand_id")
    country_id = request.args.get("country_id")
    currency_id = request.args.get("currency_id")
    if not brand_id or not currency_id:
        flash("Please select brand and currency to search.", "warning")
        return redirect(url_for("client.search"))
    # Store selected currency in session
    session["search_currency_id"] = currency_id
    currency = query_db("SELECT * FROM currencies WHERE id=?", (currency_id,), one=True)
    # Get products available in this catalogue for this client
    q = """SELECT DISTINCT p.id, p.name as product_name, p.validity_days,
                  b.name as brand_name, co.name as country_name,
                  d.id as denomination_id, d.label as denomination_label, d.value as denom_value,
                  cu.code as brand_currency_code,
                  cp.client_rate_type, cp.client_rate_value, cp.min_markup_pct, cp.id as cat_prod_id
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
        q += " AND co.id=?"
        args.append(country_id)
    q += " ORDER BY b.name, p.name"
    products = query_db(q, args)
    results = []
    for p in products:
        supplier_rates = get_best_supplier_rate(
            p["id"], p["denomination_id"], currency["code"], client["fx_buffer_pct"]
        )
        if supplier_rates:
            best = supplier_rates[0]
            if best["cost_price_converted"] == 0:
                continue
            cat_prod = {"client_rate_type": p["client_rate_type"], "client_rate_value": p["client_rate_value"]}
            selling_price = get_client_selling_price(
                best["cost_price_converted"], cat_prod, p["min_markup_pct"]
            )
            results.append({
                "product_id": p["id"],
                "product_name": p["product_name"],
                "brand_name": p["brand_name"],
                "country_name": p["country_name"],
                "denomination_id": p["denomination_id"],
                "denomination_label": p["denomination_label"],
                "validity_days": p["validity_days"],
                "supplier_id": best["supplier_id"],
                "supplier_rate_id": best["supplier_rate_id"],
                "cost_price": best["cost_price_converted"],
                "selling_price": selling_price,
                "stock_count": best["stock_count"],
                "currency_code": currency["code"],
                "currency_id": currency_id,
                "in_stock": best["stock_count"] > 0,
            })
        else:
            results.append({
                "product_id": p["id"],
                "product_name": p["product_name"],
                "brand_name": p["brand_name"],
                "country_name": p["country_name"],
                "denomination_id": p["denomination_id"],
                "denomination_label": p["denomination_label"],
                "validity_days": p["validity_days"],
                "supplier_id": None,
                "selling_price": None,
                "stock_count": 0,
                "currency_code": currency["code"],
                "currency_id": currency_id,
                "in_stock": False,
            })
    bal_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                       (client_id, currency_id), one=True)
    balance = bal_row["balance"] if bal_row else 0
    return render_template("client/search_results.html", results=results, currency=currency,
                           balance=balance, brand_id=brand_id, country_id=country_id)

@client_bp.route("/cart")
@login_required
@role_required("client")
def cart():
    cart_items = session.get("cart", [])
    return render_template("client/cart.html", cart_items=cart_items)

@client_bp.route("/cart/add", methods=["POST"])
@login_required
@role_required("client")
def cart_add():
    product_id = int(request.form.get("product_id"))
    denomination_id = int(request.form.get("denomination_id"))
    supplier_id = int(request.form.get("supplier_id", 0))
    supplier_rate_id = request.form.get("supplier_rate_id")
    cost_price = float(request.form.get("cost_price", 0))
    selling_price = float(request.form.get("selling_price"))
    qty = int(request.form.get("qty", 1))
    currency_id = request.form.get("currency_id")
    currency_code = request.form.get("currency_code")
    product_name = request.form.get("product_name")
    denomination_label = request.form.get("denomination_label")
    order_type = request.form.get("order_type", "api")
    cart = session.get("cart", [])
    # Check if already in cart
    for item in cart:
        if item["product_id"] == product_id and item["denomination_id"] == denomination_id:
            item["qty"] += qty
            session["cart"] = cart
            flash("Quantity updated in cart.", "success")
            return redirect(url_for("client.cart"))
    cart.append({
        "product_id": product_id, "denomination_id": denomination_id,
        "supplier_id": supplier_id, "supplier_rate_id": supplier_rate_id,
        "cost_price": cost_price, "selling_price": selling_price,
        "qty": qty, "currency_id": currency_id, "currency_code": currency_code,
        "product_name": product_name, "denomination_label": denomination_label,
        "order_type": order_type
    })
    session["cart"] = cart
    flash("Added to cart.", "success")
    return redirect(url_for("client.cart"))

@client_bp.route("/cart/remove/<int:idx>")
@login_required
@role_required("client")
def cart_remove(idx):
    cart = session.get("cart", [])
    if 0 <= idx < len(cart):
        cart.pop(idx)
    session["cart"] = cart
    return redirect(url_for("client.cart"))

@client_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@role_required("client")
def checkout():
    client_id = session.get("client_id")
    cart_items = session.get("cart", [])
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("client.search"))
    currency_id = cart_items[0]["currency_id"]
    currency_code = cart_items[0]["currency_code"]
    total = sum(i["selling_price"] * i["qty"] for i in cart_items)
    bal_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                       (client_id, currency_id), one=True)
    balance = bal_row["balance"] if bal_row else 0
    if request.method == "POST":
        items = [{
            "product_id": i["product_id"],
            "denomination_id": i["denomination_id"],
            "supplier_id": i["supplier_id"],
            "supplier_rate_id": i["supplier_rate_id"],
            "qty": i["qty"],
            "cost_price": i["cost_price"],
            "selling_price": i["selling_price"],
        } for i in cart_items]
        order_id, err = create_order(
            client_id, currency_id, "api", items, session.get("user_id")
        )
        if err:
            flash(f"Order failed: {err}", "danger")
            return render_template("client/checkout.html", cart_items=cart_items,
                                   total=total, balance=balance, currency_code=currency_code)
        session["cart"] = []
        flash("Order placed successfully!", "success")
        return redirect(url_for("client_orders.order_detail", order_id=order_id))
    return render_template("client/checkout.html", cart_items=cart_items,
                           total=total, balance=balance, currency_code=currency_code)

@client_bp.route("/notifications")
@login_required
@role_required("client")
def notifications():
    user_id = session.get("user_id")
    notifs = get_user_notifications(user_id)
    mark_all_read(user_id)
    return render_template("client/notifications.html", notifs=notifs)

@client_bp.route("/profile")
@login_required
@role_required("client")
def profile():
    client_id = session.get("client_id")
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    return render_template("client/profile.html", client=client)

@client_bp.route("/catalogue/download")
@login_required
@role_required("client")
def catalogue_download():
    client_id = session.get("client_id")
    rows = query_db("""
        SELECT b.name as Brand, co.name as Country, p.name as Product,
               d.label as Denomination, cu.code as Currency,
               cp.client_rate_type as RateType, cp.client_rate_value as RateValue
        FROM client_catalogues cc
        JOIN catalogues cat ON cat.id=cc.catalogue_id
        JOIN catalogue_products cp ON cp.catalogue_id=cat.id AND cp.is_active=1
        JOIN products p ON p.id=cp.product_id
        JOIN brands b ON b.id=p.brand_id JOIN countries co ON co.id=p.country_id
        JOIN currencies cu ON cu.id=p.currency_id JOIN denominations d ON d.id=cp.denomination_id
        WHERE cc.client_id=? ORDER BY b.name, co.name, p.name
    """, (client_id,))
    headers = ["Brand", "Country", "Product", "Denomination", "Currency", "Rate Type", "Rate Value"]
    data = [[r["Brand"], r["Country"], r["Product"], r["Denomination"],
             r["Currency"], r["RateType"], r["RateValue"]] for r in rows]
    return export_xlsx(headers, data, filename="my_price_list.xlsx")
