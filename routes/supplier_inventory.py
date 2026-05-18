from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from services.voucher_service import bulk_upload_codes
import csv, io

supplier_inv_bp = Blueprint("supplier_inv", __name__, url_prefix="/supplier/upload")

@supplier_inv_bp.route("/", methods=["GET", "POST"])
@login_required
@role_required("supplier")
def upload():
    supplier_id = session.get("supplier_id")
    products = query_db("SELECT p.*, b.name as brand_name FROM products p JOIN brands b ON b.id=p.brand_id WHERE p.is_active=1 ORDER BY b.name, p.name")
    denominations = query_db("SELECT * FROM denominations WHERE is_active=1")
    if request.method == "POST":
        product_id = request.form.get("product_id")
        denomination_id = request.form.get("denomination_id")
        cost_price = float(request.form.get("cost_price", 0))
        codes_text = request.form.get("codes", "").strip()
        file = request.files.get("csv_file")
        codes = []
        if file and file.filename:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            reader = csv.DictReader(stream)
            for row in reader:
                codes.append({"code": row.get("code", "").strip(), "pin": row.get("pin", "").strip() or None})
        elif codes_text:
            for line in codes_text.splitlines():
                parts = line.strip().split(",")
                if parts[0].strip():
                    codes.append({"code": parts[0].strip(), "pin": parts[1].strip() if len(parts) > 1 else None})
        if codes:
            count = bulk_upload_codes(int(product_id), int(denomination_id), supplier_id, codes, cost_price)
            flash(f"Uploaded {count} voucher codes.", "success")
        else:
            flash("No valid codes found.", "danger")
        return redirect(url_for("supplier.inventory"))
    return render_template("supplier/inventory_upload.html", products=products, denominations=denominations)
