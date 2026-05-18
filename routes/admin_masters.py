from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from datetime import datetime

masters_bp = Blueprint("masters", __name__, url_prefix="/admin/masters")

# ─── COUNTRY ───────────────────────────────────────
@masters_bp.route("/countries")
@login_required
@role_required("superadmin", "internal")
def countries():
    rows = query_db("SELECT * FROM countries ORDER BY name")
    return render_template("admin/masters_country.html", rows=rows)

@masters_bp.route("/countries/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def country_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()
    if not name or not code:
        flash("Name and code are required.", "danger")
        return redirect(url_for("masters.countries"))
    if id_:
        old = query_db("SELECT * FROM countries WHERE id=?", (id_,), one=True)
        execute_db("UPDATE countries SET name=?, code=?, updated_at=? WHERE id=?",
                   (name, code, datetime.utcnow(), id_))
        log_action("edit", "countries", id_, dict(old), {"name": name, "code": code})
        flash("Country updated.", "success")
    else:
        new_id = execute_db("INSERT INTO countries (name, code) VALUES (?,?)", (name, code))
        log_action("add", "countries", new_id, None, {"name": name, "code": code})
        flash("Country added.", "success")
    return redirect(url_for("masters.countries"))

@masters_bp.route("/countries/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def country_toggle(id):
    row = query_db("SELECT is_active FROM countries WHERE id=?", (id,), one=True)
    new_status = 0 if row["is_active"] else 1
    execute_db("UPDATE countries SET is_active=?, updated_at=? WHERE id=?", (new_status, datetime.utcnow(), id))
    log_action("toggle", "countries", id, {"is_active": row["is_active"]}, {"is_active": new_status})
    flash("Country status updated.", "success")
    return redirect(url_for("masters.countries"))

# ─── CURRENCY ──────────────────────────────────────
@masters_bp.route("/currencies")
@login_required
@role_required("superadmin", "internal")
def currencies():
    rows = query_db("SELECT * FROM currencies ORDER BY name")
    return render_template("admin/masters_currency.html", rows=rows)

@masters_bp.route("/currencies/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def currency_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()
    symbol = request.form.get("symbol", "").strip()
    if not name or not code or not symbol:
        flash("All fields required.", "danger")
        return redirect(url_for("masters.currencies"))
    if id_:
        execute_db("UPDATE currencies SET name=?, code=?, symbol=?, updated_at=? WHERE id=?",
                   (name, code, symbol, datetime.utcnow(), id_))
        flash("Currency updated.", "success")
    else:
        execute_db("INSERT INTO currencies (name, code, symbol) VALUES (?,?,?)", (name, code, symbol))
        flash("Currency added.", "success")
    log_action("save", "currencies", id_)
    return redirect(url_for("masters.currencies"))

@masters_bp.route("/currencies/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def currency_toggle(id):
    row = query_db("SELECT is_active FROM currencies WHERE id=?", (id,), one=True)
    execute_db("UPDATE currencies SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Currency status updated.", "success")
    return redirect(url_for("masters.currencies"))

# ─── DENOMINATION ──────────────────────────────────
@masters_bp.route("/denominations")
@login_required
@role_required("superadmin", "internal")
def denominations():
    rows = query_db("SELECT * FROM denominations ORDER BY type, value")
    return render_template("admin/masters_denomination.html", rows=rows)

@masters_bp.route("/denominations/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def denomination_save():
    id_ = request.form.get("id")
    type_ = request.form.get("type")
    label = request.form.get("label", "").strip()
    value = request.form.get("value") or None
    range_from = request.form.get("range_from") or None
    range_to = request.form.get("range_to") or None
    if id_:
        execute_db("UPDATE denominations SET type=?, label=?, value=?, range_from=?, range_to=?, updated_at=? WHERE id=?",
                   (type_, label, value, range_from, range_to, datetime.utcnow(), id_))
        flash("Denomination updated.", "success")
    else:
        execute_db("INSERT INTO denominations (type, label, value, range_from, range_to) VALUES (?,?,?,?,?)",
                   (type_, label, value, range_from, range_to))
        flash("Denomination added.", "success")
    log_action("save", "denominations", id_)
    return redirect(url_for("masters.denominations"))

@masters_bp.route("/denominations/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def denomination_toggle(id):
    row = query_db("SELECT is_active FROM denominations WHERE id=?", (id,), one=True)
    execute_db("UPDATE denominations SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Status updated.", "success")
    return redirect(url_for("masters.denominations"))

# ─── BRAND ─────────────────────────────────────────
@masters_bp.route("/brands")
@login_required
@role_required("superadmin", "internal")
def brands():
    rows = query_db("""
        SELECT b.*, GROUP_CONCAT(c.name, ', ') as countries
        FROM brands b
        LEFT JOIN brand_countries bc ON bc.brand_id = b.id
        LEFT JOIN countries c ON c.id = bc.country_id
        GROUP BY b.id ORDER BY b.name
    """)
    all_countries = query_db("SELECT * FROM countries WHERE is_active=1 ORDER BY name")
    return render_template("admin/masters_brand.html", rows=rows, all_countries=all_countries)

@masters_bp.route("/brands/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def brand_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    country_ids = request.form.getlist("country_ids")
    if not name:
        flash("Brand name required.", "danger")
        return redirect(url_for("masters.brands"))
    if id_:
        execute_db("UPDATE brands SET name=?, updated_at=? WHERE id=?", (name, datetime.utcnow(), id_))
        execute_db("DELETE FROM brand_countries WHERE brand_id=?", (id_,))
        bid = id_
    else:
        bid = execute_db("INSERT INTO brands (name) VALUES (?)", (name,))
    for cid in country_ids:
        try:
            execute_db("INSERT INTO brand_countries (brand_id, country_id) VALUES (?,?)", (bid, cid))
        except Exception:
            pass
    log_action("save", "brands", bid)
    flash("Brand saved.", "success")
    return redirect(url_for("masters.brands"))

@masters_bp.route("/brands/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def brand_toggle(id):
    row = query_db("SELECT is_active FROM brands WHERE id=?", (id,), one=True)
    execute_db("UPDATE brands SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Brand status updated.", "success")
    return redirect(url_for("masters.brands"))

# ─── PRODUCT ───────────────────────────────────────
@masters_bp.route("/products")
@login_required
@role_required("superadmin", "internal")
def products():
    rows = query_db("""
        SELECT p.*, b.name as brand_name, c.name as country_name,
               cu.code as currency_code, d.label as denomination_label
        FROM products p
        JOIN brands b ON b.id = p.brand_id
        JOIN countries c ON c.id = p.country_id
        JOIN currencies cu ON cu.id = p.currency_id
        JOIN denominations d ON d.id = p.denomination_id
        ORDER BY b.name, p.name
    """)
    brands = query_db("SELECT * FROM brands WHERE is_active=1 ORDER BY name")
    countries = query_db("SELECT * FROM countries WHERE is_active=1 ORDER BY name")
    currencies = query_db("SELECT * FROM currencies WHERE is_active=1 ORDER BY name")
    denominations = query_db("SELECT * FROM denominations WHERE is_active=1 ORDER BY type, value")
    return render_template("admin/masters_product.html", rows=rows,
                           brands=brands, countries=countries,
                           currencies=currencies, denominations=denominations)

@masters_bp.route("/products/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def product_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    product_code = request.form.get("product_code", "").strip().upper()
    brand_id = request.form.get("brand_id")
    country_id = request.form.get("country_id")
    currency_id = request.form.get("currency_id")
    denomination_id = request.form.get("denomination_id")
    validity_days = request.form.get("validity_days") or None
    if not all([name, product_code, brand_id, country_id, currency_id, denomination_id]):
        flash("All required fields must be filled.", "danger")
        return redirect(url_for("masters.products"))
    if id_:
        execute_db("""UPDATE products SET name=?, product_code=?, brand_id=?, country_id=?,
                      currency_id=?, denomination_id=?, validity_days=?, updated_at=? WHERE id=?""",
                   (name, product_code, brand_id, country_id, currency_id, denomination_id,
                    validity_days, datetime.utcnow(), id_))
        flash("Product updated.", "success")
    else:
        try:
            execute_db("""INSERT INTO products (name, product_code, brand_id, country_id, currency_id, denomination_id, validity_days)
                          VALUES (?,?,?,?,?,?,?)""",
                       (name, product_code, brand_id, country_id, currency_id, denomination_id, validity_days))
            flash("Product added.", "success")
        except Exception:
            flash("Product name or code already exists.", "danger")
    log_action("save", "products", id_)
    return redirect(url_for("masters.products"))

@masters_bp.route("/products/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def product_toggle(id):
    row = query_db("SELECT is_active FROM products WHERE id=?", (id,), one=True)
    execute_db("UPDATE products SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Product status updated.", "success")
    return redirect(url_for("masters.products"))

@masters_bp.route("/products/delete/<int:id>")
@login_required
@role_required("superadmin", "internal")
def product_delete(id):
    prod = query_db("SELECT * FROM products WHERE id=?", (id,), one=True)
    if prod:
        execute_db("DELETE FROM catalogue_products WHERE product_id=?", (id,))
        execute_db("DELETE FROM supplier_rates WHERE product_id=?", (id,))
        execute_db("DELETE FROM voucher_codes WHERE product_id=?", (id,))
        execute_db("DELETE FROM order_items WHERE product_id=?", (id,))
        execute_db("DELETE FROM inventory_orders WHERE product_id=?", (id,))
        execute_db("DELETE FROM products WHERE id=?", (id,))
        log_action("delete", "products", id, dict(prod), None)
        flash(f"Product '{prod['name']}' has been permanently deleted.", "success")
    else:
        flash("Product not found.", "danger")
    return redirect(url_for("masters.products"))

# ─── SUPPLIER ──────────────────────────────────────
@masters_bp.route("/suppliers")
@login_required
@role_required("superadmin", "internal")
def suppliers():
    rows = query_db("""
        SELECT s.*, c.name as country_name
        FROM suppliers s LEFT JOIN countries c ON c.id = s.country_id
        ORDER BY s.name
    """)
    countries = query_db("SELECT * FROM countries WHERE is_active=1 ORDER BY name")
    currencies = query_db("SELECT * FROM currencies WHERE is_active=1 ORDER BY name")
    return render_template("admin/masters_supplier.html", rows=rows, countries=countries, currencies=currencies)

@masters_bp.route("/suppliers/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def supplier_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    supplier_code = request.form.get("supplier_code", "").strip().upper()
    country_id = request.form.get("country_id") or None
    address = request.form.get("address", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    api_endpoint = request.form.get("api_endpoint", "").strip()
    api_key = request.form.get("api_key", "").strip()
    api_enabled = 1 if request.form.get("api_enabled") else 0
    if not name or not supplier_code:
        flash("Name and code required.", "danger")
        return redirect(url_for("masters.suppliers"))
    if id_:
        execute_db("""UPDATE suppliers SET name=?, supplier_code=?, country_id=?, address=?,
                      contact_email=?, api_endpoint=?, api_key=?, api_enabled=?, updated_at=? WHERE id=?""",
                   (name, supplier_code, country_id, address, contact_email,
                    api_endpoint, api_key, api_enabled, datetime.utcnow(), id_))
        flash("Supplier updated.", "success")
    else:
        try:
            sid = execute_db("""INSERT INTO suppliers (name, supplier_code, country_id, address, contact_email, api_endpoint, api_key, api_enabled)
                          VALUES (?,?,?,?,?,?,?,?)""",
                       (name, supplier_code, country_id, address, contact_email, api_endpoint, api_key, api_enabled))
            # Create fund balance slots for active currencies
            currencies = query_db("SELECT id FROM currencies WHERE is_active=1")
            for c in currencies:
                try:
                    execute_db("INSERT INTO supplier_fund_balances (supplier_id, currency_id) VALUES (?,?)", (sid, c["id"]))
                except Exception:
                    pass
            flash("Supplier added.", "success")
        except Exception:
            flash("Supplier name or code already exists.", "danger")
    log_action("save", "suppliers", id_)
    return redirect(url_for("masters.suppliers"))

@masters_bp.route("/suppliers/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def supplier_toggle(id):
    row = query_db("SELECT is_active FROM suppliers WHERE id=?", (id,), one=True)
    execute_db("UPDATE suppliers SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Supplier status updated.", "success")
    return redirect(url_for("masters.suppliers"))

# ─── CLIENT ────────────────────────────────────────
@masters_bp.route("/clients")
@login_required
@role_required("superadmin", "internal")
def clients():
    rows = query_db("""
        SELECT c.*, co.name as country_name, cu.code as default_currency_code
        FROM clients c
        LEFT JOIN countries co ON co.id = c.country_id
        LEFT JOIN currencies cu ON cu.id = c.default_currency_id
        ORDER BY c.name
    """)
    countries = query_db("SELECT * FROM countries WHERE is_active=1 ORDER BY name")
    currencies = query_db("SELECT * FROM currencies WHERE is_active=1 ORDER BY name")
    return render_template("admin/masters_client.html", rows=rows, countries=countries, currencies=currencies)

@masters_bp.route("/clients/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def client_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    client_code = request.form.get("client_code", "").strip().upper()
    country_id = request.form.get("country_id") or None
    address = request.form.get("address", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    default_currency_id = request.form.get("default_currency_id") or None
    fx_buffer_pct = float(request.form.get("fx_buffer_pct", 1.0))
    currency_ids = request.form.getlist("currency_ids")
    login_enabled = 1 if request.form.get("login_enabled") else 0
    credit_enabled = 1 if request.form.get("credit_enabled") else 0
    credit_limit = float(request.form.get("credit_limit", 0))
    if not name or not client_code:
        flash("Name and code required.", "danger")
        return redirect(url_for("masters.clients"))
    if id_:
        execute_db("""UPDATE clients SET name=?, client_code=?, country_id=?, address=?, email=?, phone=?,
                      default_currency_id=?, fx_buffer_pct=?, login_enabled=?, credit_enabled=?, credit_limit=?, updated_at=?
                      WHERE id=?""",
                   (name, client_code, country_id, address, email, phone,
                    default_currency_id, fx_buffer_pct, login_enabled, credit_enabled, credit_limit, datetime.utcnow(), id_))
        cid = id_
        flash("Client updated.", "success")
    else:
        try:
            cid = execute_db("""INSERT INTO clients (name, client_code, country_id, address, email, phone,
                                default_currency_id, fx_buffer_pct, login_enabled, credit_enabled, credit_limit)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                             (name, client_code, country_id, address, email, phone,
                              default_currency_id, fx_buffer_pct, login_enabled, credit_enabled, credit_limit))
            flash("Client added.", "success")
        except Exception:
            flash("Client name or code already exists.", "danger")
            return redirect(url_for("masters.clients"))
    # Update currencies
    execute_db("DELETE FROM client_currencies WHERE client_id=?", (cid,))
    execute_db("DELETE FROM client_fund_balances WHERE client_id=?", (cid,))
    for curr_id in currency_ids:
        is_def = 1 if str(curr_id) == str(default_currency_id) else 0
        try:
            execute_db("INSERT INTO client_currencies (client_id, currency_id, is_default) VALUES (?,?,?)",
                       (cid, curr_id, is_def))
            execute_db("INSERT OR IGNORE INTO client_fund_balances (client_id, currency_id) VALUES (?,?)",
                       (cid, curr_id))
        except Exception:
            pass
    log_action("save", "clients", cid)
    return redirect(url_for("masters.clients"))

@masters_bp.route("/clients/toggle/<int:id>")
@login_required
@role_required("superadmin", "internal")
def client_toggle(id):
    row = query_db("SELECT is_active FROM clients WHERE id=?", (id,), one=True)
    execute_db("UPDATE clients SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("Client status updated.", "success")
    return redirect(url_for("masters.clients"))

@masters_bp.route("/clients/<int:client_id>/users")
@login_required
@role_required("superadmin", "internal")
def client_users(client_id):
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    users = query_db("SELECT * FROM users WHERE client_id=? ORDER BY name", (client_id,))
    return render_template("admin/masters_client.html", client=client, client_users=users, view="users")
