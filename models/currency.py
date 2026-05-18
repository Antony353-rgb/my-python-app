from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = "SELECT * FROM currencies"
    if active_only:
        q += " WHERE is_active=1"
    return query_db(q + " ORDER BY name")

def get_by_id(id):
    return query_db("SELECT * FROM currencies WHERE id=?", (id,), one=True)

def get_by_code(code):
    return query_db("SELECT * FROM currencies WHERE code=?", (code,), one=True)

def create(name, code, symbol):
    return execute_db("INSERT INTO currencies (name,code,symbol) VALUES (?,?,?)", (name, code.upper(), symbol))

def update(id, name, code, symbol):
    execute_db("UPDATE currencies SET name=?,code=?,symbol=?,updated_at=? WHERE id=?",
               (name, code.upper(), symbol, datetime.utcnow(), id))

def toggle(id):
    row = get_by_id(id)
    if row:
        execute_db("UPDATE currencies SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
