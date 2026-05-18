from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = """SELECT c.*, co.name as country_name, cu.code as default_currency_code
           FROM clients c
           LEFT JOIN countries co ON co.id=c.country_id
           LEFT JOIN currencies cu ON cu.id=c.default_currency_id"""
    if active_only:
        q += " WHERE c.is_active=1"
    return query_db(q + " ORDER BY c.name")

def get_by_id(id):
    return query_db("""SELECT c.*, co.name as country_name, cu.code as default_currency_code
                       FROM clients c
                       LEFT JOIN countries co ON co.id=c.country_id
                       LEFT JOIN currencies cu ON cu.id=c.default_currency_id
                       WHERE c.id=?""", (id,), one=True)

def get_currencies(client_id):
    return query_db("""SELECT cu.* FROM client_currencies cc
                       JOIN currencies cu ON cu.id=cc.currency_id
                       WHERE cc.client_id=? ORDER BY cc.is_default DESC, cu.code""", (client_id,))

def get_catalogues(client_id):
    return query_db("""SELECT cat.*, s.name as supplier_name FROM client_catalogues cc
                       JOIN catalogues cat ON cat.id=cc.catalogue_id
                       JOIN suppliers s ON s.id=cat.supplier_id
                       WHERE cc.client_id=?""", (client_id,))

def toggle(id):
    row = query_db("SELECT is_active FROM clients WHERE id=?", (id,), one=True)
    if row:
        execute_db("UPDATE clients SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
