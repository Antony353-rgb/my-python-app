from database.db import query_db, execute_db
from datetime import datetime

def get_all():
    return query_db("""SELECT c.*, s.name as supplier_name,
                              COUNT(cp.id) as product_count
                       FROM catalogues c JOIN suppliers s ON s.id=c.supplier_id
                       LEFT JOIN catalogue_products cp ON cp.catalogue_id=c.id AND cp.is_active=1
                       GROUP BY c.id ORDER BY c.name""")

def get_by_id(id):
    return query_db("""SELECT c.*, s.name as supplier_name
                       FROM catalogues c JOIN suppliers s ON s.id=c.supplier_id WHERE c.id=?""", (id,), one=True)

def get_products(catalogue_id):
    return query_db("""SELECT cp.*, p.name as product_name, b.name as brand_name,
                              co.name as country_name, d.label as denomination_label, cu.code as currency_code
                       FROM catalogue_products cp
                       JOIN products p ON p.id=cp.product_id
                       JOIN brands b ON b.id=p.brand_id
                       JOIN countries co ON co.id=p.country_id
                       JOIN currencies cu ON cu.id=p.currency_id
                       JOIN denominations d ON d.id=cp.denomination_id
                       WHERE cp.catalogue_id=? ORDER BY b.name, p.name""", (catalogue_id,))

def get_mapped_clients(catalogue_id):
    return query_db("""SELECT c.id, c.name FROM client_catalogues cc
                       JOIN clients c ON c.id=cc.client_id WHERE cc.catalogue_id=?""", (catalogue_id,))

def create(name, supplier_id, catalogue_type="standard"):
    return execute_db("INSERT INTO catalogues (name,supplier_id,catalogue_type) VALUES (?,?,?)",
                      (name, supplier_id, catalogue_type))

def add_product(catalogue_id, product_id, denomination_id, sup_rate_type=None, sup_rate_value=None,
                client_rate_type=None, client_rate_value=None, min_markup_pct=0):
    try:
        execute_db("""INSERT INTO catalogue_products
                      (catalogue_id,product_id,denomination_id,supplier_rate_type,supplier_rate_value,
                       client_rate_type,client_rate_value,min_markup_pct)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (catalogue_id, product_id, denomination_id, sup_rate_type, sup_rate_value,
                    client_rate_type, client_rate_value, min_markup_pct))
        return True
    except Exception:
        return False

def map_client(client_id, catalogue_id):
    try:
        execute_db("INSERT INTO client_catalogues (client_id,catalogue_id) VALUES (?,?)", (client_id, catalogue_id))
        return True
    except Exception:
        return False
