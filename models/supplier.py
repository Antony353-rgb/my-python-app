from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = """SELECT s.*, c.name as country_name FROM suppliers s
           LEFT JOIN countries c ON c.id=s.country_id"""
    if active_only:
        q += " WHERE s.is_active=1"
    return query_db(q + " ORDER BY s.name")

def get_by_id(id):
    return query_db("""SELECT s.*, c.name as country_name FROM suppliers s
                       LEFT JOIN countries c ON c.id=s.country_id WHERE s.id=?""", (id,), one=True)

def create(name, supplier_code, country_id=None, address=None, contact_email=None,
           api_endpoint=None, api_key=None, api_enabled=0):
    try:
        sid = execute_db(
            "INSERT INTO suppliers (name,supplier_code,country_id,address,contact_email,api_endpoint,api_key,api_enabled) VALUES (?,?,?,?,?,?,?,?)",
            (name, supplier_code.upper(), country_id, address, contact_email, api_endpoint, api_key, api_enabled)
        )
        currencies = query_db("SELECT id FROM currencies WHERE is_active=1")
        for c in currencies:
            try:
                execute_db("INSERT INTO supplier_fund_balances (supplier_id,currency_id) VALUES (?,?)", (sid, c["id"]))
            except Exception:
                pass
        return sid
    except Exception:
        return None

def update(id, **kwargs):
    kwargs["updated_at"] = datetime.utcnow()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [id]
    execute_db(f"UPDATE suppliers SET {sets} WHERE id=?", vals)

def toggle(id):
    row = query_db("SELECT is_active FROM suppliers WHERE id=?", (id,), one=True)
    if row:
        execute_db("UPDATE suppliers SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
