from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from utils.export import export_xlsx
from datetime import datetime

catalogue_bp = Blueprint("catalogue", __name__, url_prefix="/admin/catalogue")

@catalogue_bp.route("/")
@login_required
@role_required("superadmin", "internal")
def catalogue_list():
    catalogues = query_db("""
        SELECT c.*, s.name as supplier_name,
               COUNT(cp.id) as product_count
        FROM catalogues c
        JOIN suppliers s ON s.id=c.supplier_id
        LEFT JOIN catalogue_products cp ON cp.catalogue_id=c.id AND cp.is_active=1
        GROUP BY c.id ORDER BY c.name
    """)
    suppliers = query_db("SELECT * FROM suppliers WHERE is_active=1 ORDER BY name")
    return render_template("admin/catalogue_list.html", catalogues=catalogues, suppliers=suppliers)

@catalogue_bp.route("/save", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def catalogue_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    supplier_id = request.form.get("supplier_id")
    catalogue_type = request.form.get("catalogue_type", "standard")
    if not name or not supplier_id:
        flash("Name and supplier required.", "danger")
        return redirect(url_for("catalogue.catalogue_list"))
    if id_:
        execute_db("UPDATE catalogues SET name=?, supplier_id=?, catalogue_type=?, updated_at=? WHERE id=?",
                   (name, supplier_id, catalogue_type, datetime.utcnow(), id_))
        flash("Catalogue updated.", "success")
    else:
        execute_db("INSERT INTO catalogues (name, supplier_id, catalogue_type) VALUES (?,?,?)",
                   (name, supplier_id, catalogue_type))
        flash("Catalogue created.", "success")
    log_action("save", "catalogue", id_)
    return redirect(url_for("catalogue.catalogue_list"))

@catalogue_bp.route("/<int:cat_id>")
@login_required
@role_required("superadmin", "internal")
def catalogue_detail(cat_id):
    cat = query_db("SELECT c.*, s.name as supplier_name FROM catalogues c JOIN suppliers s ON s.id=c.supplier_id WHERE c.id=?",
                   (cat_id,), one=True)
    products = query_db("""
        SELECT cp.*, p.name as product_name, b.name as brand_name,
               co.name as country_name, d.label as denomination_label, cu.code as currency_code
        FROM catalogue_products cp
        JOIN products p ON p.id=cp.product_id
        JOIN brands b ON b.id=p.brand_id
        JOIN countries co ON co.id=p.country_id
        JOIN currencies cu ON cu.id=p.currency_id
        JOIN denominations d ON d.id=cp.denomination_id
        WHERE cp.catalogue_id=?
        ORDER BY b.name, p.name
    """, (cat_id,))
    all_products = query_db("""
        SELECT p.*, b.name as brand_name, co.name as country_name, d.label as denomination_label
        FROM products p JOIN brands b ON b.id=p.brand_id
        JOIN countries co ON co.id=p.country_id JOIN denominations d ON d.id=p.denomination_id
        WHERE p.is_active=1 ORDER BY b.name, p.name
    """)
    all_denominations = query_db("SELECT * FROM denominations WHERE is_active=1")
    # Clients mapped to this catalogue
    mapped_clients = query_db("""
        SELECT c.name, c.id FROM client_catalogues cc
        JOIN clients c ON c.id=cc.client_id WHERE cc.catalogue_id=?
    """, (cat_id,))
    all_clients = query_db("SELECT * FROM clients WHERE is_active=1 ORDER BY name")
    return render_template("admin/catalogue_detail.html", cat=cat, products=products,
                           all_products=all_products, all_denominations=all_denominations,
                           mapped_clients=mapped_clients, all_clients=all_clients)

@catalogue_bp.route("/<int:cat_id>/add-product", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def catalogue_add_product(cat_id):
    product_id = request.form.get("product_id")
    denomination_id = request.form.get("denomination_id")
    sup_rate_type = request.form.get("sup_rate_type")
    sup_rate_value = request.form.get("sup_rate_value") or None
    client_rate_type = request.form.get("client_rate_type")
    client_rate_value = request.form.get("client_rate_value") or None
    min_markup_pct = float(request.form.get("min_markup_pct", 0))
    # Check not already mapped to same client in another catalogue
    try:
        execute_db("""INSERT INTO catalogue_products
                      (catalogue_id, product_id, denomination_id, supplier_rate_type, supplier_rate_value,
                       client_rate_type, client_rate_value, min_markup_pct)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (cat_id, product_id, denomination_id, sup_rate_type, sup_rate_value,
                    client_rate_type, client_rate_value, min_markup_pct))
        flash("Product added to catalogue.", "success")
    except Exception:
        flash("Product with this denomination already in catalogue.", "danger")
    return redirect(url_for("catalogue.catalogue_detail", cat_id=cat_id))

@catalogue_bp.route("/product/<int:cp_id>/toggle")
@login_required
@role_required("superadmin", "internal")
def catalogue_product_toggle(cp_id):
    row = query_db("SELECT is_active, catalogue_id FROM catalogue_products WHERE id=?", (cp_id,), one=True)
    execute_db("UPDATE catalogue_products SET is_active=? WHERE id=?", (1 - row["is_active"], cp_id))
    flash("Product status updated.", "success")
    return redirect(url_for("catalogue.catalogue_detail", cat_id=row["catalogue_id"]))

@catalogue_bp.route("/<int:cat_id>/map-client", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def map_client(cat_id):
    client_id = request.form.get("client_id")
    try:
        execute_db("INSERT INTO client_catalogues (client_id, catalogue_id) VALUES (?,?)", (client_id, cat_id))
        flash("Client mapped to catalogue.", "success")
    except Exception:
        flash("Client is already mapped to this catalogue.", "warning")
    return redirect(url_for("catalogue.catalogue_detail", cat_id=cat_id))

@catalogue_bp.route("/<int:cat_id>/unmap-client/<int:client_id>")
@login_required
@role_required("superadmin")
def unmap_client(cat_id, client_id):
    execute_db("DELETE FROM client_catalogues WHERE catalogue_id=? AND client_id=?", (cat_id, client_id))
    flash("Client unmapped.", "success")
    return redirect(url_for("catalogue.catalogue_detail", cat_id=cat_id))

@catalogue_bp.route("/download/<int:client_id>")
@login_required
@role_required("superadmin", "internal")
def download_client_catalogue(client_id):
    client = query_db("SELECT * FROM clients WHERE id=?", (client_id,), one=True)
    rows = query_db("""
        SELECT b.name as Brand, co.name as Country, p.name as Product,
               d.label as Denomination, cu.code as Currency,
               cp.client_rate_type as RateType, cp.client_rate_value as RateValue,
               cp.min_markup_pct as MinMarkup
        FROM client_catalogues cc
        JOIN catalogues cat ON cat.id=cc.catalogue_id
        JOIN catalogue_products cp ON cp.catalogue_id=cat.id AND cp.is_active=1
        JOIN products p ON p.id=cp.product_id
        JOIN brands b ON b.id=p.brand_id
        JOIN countries co ON co.id=p.country_id
        JOIN currencies cu ON cu.id=p.currency_id
        JOIN denominations d ON d.id=cp.denomination_id
        WHERE cc.client_id=?
        ORDER BY b.name, co.name, p.name
    """, (client_id,))
    headers = ["Brand", "Country", "Product", "Denomination", "Currency", "RateType", "RateValue", "MinMarkup"]
    data = [[r["Brand"], r["Country"], r["Product"], r["Denomination"], r["Currency"],
             r["RateType"], r["RateValue"], r["MinMarkup"]] for r in rows]
    return export_xlsx(headers, data, sheet_name="Catalogue",
                       filename=f"catalogue_{client['client_code']}.xlsx")
