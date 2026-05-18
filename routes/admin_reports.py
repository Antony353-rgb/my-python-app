from flask import Blueprint, render_template, request
from utils.decorators import login_required, role_required
from services.report_service import funding_report, client_productivity_report, supplier_productivity_report
from services.inventory_service import get_inventory_balance
from database.db import query_db
from utils.export import export_xlsx

reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")

@reports_bp.route("/funding")
@login_required
@role_required("superadmin", "internal")
def funding():
    client_id = request.args.get("client_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    export = request.args.get("export")
    data = funding_report(client_id, date_from, date_to)
    if export == "xlsx":
        headers = ["Client", "Currency", "Type", "Amount", "Balance Before", "Balance After", "Remarks", "Date"]
        rows = [[r["client_name"], r["currency_code"], r["txn_type"], r["amount"],
                 r["balance_before"], r["balance_after"], r["remarks"], r["created_at"]] for r in data]
        return export_xlsx(headers, rows, filename="funding_report.xlsx")
    clients = query_db("SELECT id, name FROM clients ORDER BY name")
    return render_template("admin/reports_funding.html", data=data, clients=clients,
                           filters={"client_id": client_id, "date_from": date_from, "date_to": date_to})

@reports_bp.route("/client-productivity")
@login_required
@role_required("superadmin", "internal")
def client_productivity():
    client_id = request.args.get("client_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    export = request.args.get("export")
    data = client_productivity_report(client_id, date_from, date_to)
    if export == "xlsx":
        headers = ["Client", "Brand", "Country", "Product", "Denomination", "Currency", "Orders", "Qty", "Revenue", "Profit"]
        rows = [[r["client_name"], r["brand"], r["country"], r["product"], r["denomination"],
                 r["currency"], r["total_orders"], r["total_qty"], r["total_revenue"], r["total_profit"]] for r in data]
        return export_xlsx(headers, rows, filename="client_productivity.xlsx")
    clients = query_db("SELECT id, name FROM clients ORDER BY name")
    return render_template("admin/reports_client.html", data=data, clients=clients,
                           filters={"client_id": client_id, "date_from": date_from, "date_to": date_to})

@reports_bp.route("/supplier-productivity")
@login_required
@role_required("superadmin", "internal")
def supplier_productivity():
    supplier_id = request.args.get("supplier_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    export = request.args.get("export")
    data = supplier_productivity_report(supplier_id, date_from, date_to)
    if export == "xlsx":
        headers = ["Supplier", "Brand", "Country", "Product", "Denomination", "Qty", "Cost", "Revenue", "Profit"]
        rows = [[r["supplier_name"], r["brand"], r["country"], r["product"], r["denomination"],
                 r["total_qty"], r["total_cost"], r["total_selling"], r["total_profit"]] for r in data]
        return export_xlsx(headers, rows, filename="supplier_productivity.xlsx")
    suppliers = query_db("SELECT id, name FROM suppliers ORDER BY name")
    return render_template("admin/reports_supplier.html", data=data, suppliers=suppliers,
                           filters={"supplier_id": supplier_id, "date_from": date_from, "date_to": date_to})

@reports_bp.route("/inventory-balance")
@login_required
@role_required("superadmin", "internal")
def inventory_balance():
    export = request.args.get("export")
    data = get_inventory_balance()
    if export == "xlsx":
        headers = ["Product", "Brand", "Country", "Denomination", "Currency", "Supplier", "Available", "Reserved", "Sold", "Expired"]
        rows = [[r["product_name"], r["brand_name"], r["country_name"], r["denomination"],
                 r["currency"], r["supplier_name"], r["available"], r["reserved"], r["sold"], r["expired"]] for r in data]
        return export_xlsx(headers, rows, filename="inventory_balance.xlsx")
    return render_template("admin/reports_inventory.html", data=data)
