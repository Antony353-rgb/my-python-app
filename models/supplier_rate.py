from database.db import query_db, execute_db
from datetime import datetime

def get_all():
    return query_db("""SELECT sr.*, s.name as supplier_name, b.name as brand_name,
                              p.name as product_name, d.label as denomination_label, co.name as country_name
                       FROM supplier_rates sr
                       JOIN suppliers s ON s.id=sr.supplier_id
                       JOIN brands b ON b.id=sr.brand_id
                       JOIN products p ON p.id=sr.product_id
                       JOIN denominations d ON d.id=sr.denomination_id
                       JOIN countries co ON co.id=sr.country_id
                       ORDER BY s.name, b.name, p.name""")

def get_for_product(product_id, denomination_id):
    return query_db("""SELECT sr.*, s.name as supplier_name FROM supplier_rates sr
                       JOIN suppliers s ON s.id=sr.supplier_id
                       WHERE sr.product_id=? AND sr.denomination_id=? AND sr.is_active=1
                       ORDER BY sr.rate_value""", (product_id, denomination_id))

def create(supplier_id, brand_id, product_id, country_id, denomination_id,
           rate_type, rate_value, cost_price=None, effective_date=None):
    return execute_db("""INSERT INTO supplier_rates
                         (supplier_id,brand_id,product_id,country_id,denomination_id,
                          rate_type,rate_value,cost_price,effective_date)
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (supplier_id, brand_id, product_id, country_id, denomination_id,
                       rate_type, rate_value, cost_price, effective_date))

def toggle(id):
    row = query_db("SELECT is_active FROM supplier_rates WHERE id=?", (id,), one=True)
    if row:
        execute_db("UPDATE supplier_rates SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
