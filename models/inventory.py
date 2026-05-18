from database.db import query_db, execute_db
from datetime import datetime

def get_all_orders():
    return query_db("""SELECT io.*, s.name as supplier_name, p.name as product_name,
                              d.label as denomination_label
                       FROM inventory_orders io
                       JOIN suppliers s ON s.id=io.supplier_id
                       JOIN products p ON p.id=io.product_id
                       JOIN denominations d ON d.id=io.denomination_id
                       ORDER BY io.created_at DESC""")

def get_by_id(id):
    return query_db("SELECT * FROM inventory_orders WHERE id=?", (id,), one=True)

def get_pending():
    return query_db("""SELECT io.*, s.name as supplier_name, p.name as product_name
                       FROM inventory_orders io
                       JOIN suppliers s ON s.id=io.supplier_id
                       JOIN products p ON p.id=io.product_id
                       WHERE io.status IN ('pending','partial')
                       ORDER BY io.created_at""")
