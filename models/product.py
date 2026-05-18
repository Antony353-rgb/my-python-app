from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = """SELECT p.*, b.name as brand_name, c.name as country_name,
                  cu.code as currency_code, d.label as denomination_label
           FROM products p
           JOIN brands b ON b.id=p.brand_id
           JOIN countries c ON c.id=p.country_id
           JOIN currencies cu ON cu.id=p.currency_id
           JOIN denominations d ON d.id=p.denomination_id"""
    if active_only:
        q += " WHERE p.is_active=1"
    return query_db(q + " ORDER BY b.name, p.name")

def get_by_id(id):
    return query_db("""SELECT p.*, b.name as brand_name, c.name as country_name,
                              cu.code as currency_code, d.label as denomination_label
                       FROM products p
                       JOIN brands b ON b.id=p.brand_id
                       JOIN countries c ON c.id=p.country_id
                       JOIN currencies cu ON cu.id=p.currency_id
                       JOIN denominations d ON d.id=p.denomination_id
                       WHERE p.id=?""", (id,), one=True)

def create(name, product_code, brand_id, country_id, currency_id, denomination_id, validity_days=None):
    try:
        return execute_db(
            "INSERT INTO products (name,product_code,brand_id,country_id,currency_id,denomination_id,validity_days) VALUES (?,?,?,?,?,?,?)",
            (name, product_code.upper(), brand_id, country_id, currency_id, denomination_id, validity_days)
        )
    except Exception:
        return None

def update(id, **kwargs):
    kwargs["updated_at"] = datetime.utcnow()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [id]
    execute_db(f"UPDATE products SET {sets} WHERE id=?", vals)

def toggle(id):
    row = query_db("SELECT is_active FROM products WHERE id=?", (id,), one=True)
    if row:
        execute_db("UPDATE products SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
