from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = "SELECT * FROM denominations"
    if active_only:
        q += " WHERE is_active=1"
    return query_db(q + " ORDER BY type, value")

def get_by_id(id):
    return query_db("SELECT * FROM denominations WHERE id=?", (id,), one=True)

def create(type_, label, value=None, range_from=None, range_to=None):
    return execute_db(
        "INSERT INTO denominations (type,label,value,range_from,range_to) VALUES (?,?,?,?,?)",
        (type_, label, value, range_from, range_to)
    )

def update(id, type_, label, value=None, range_from=None, range_to=None):
    execute_db("UPDATE denominations SET type=?,label=?,value=?,range_from=?,range_to=?,updated_at=? WHERE id=?",
               (type_, label, value, range_from, range_to, datetime.utcnow(), id))

def toggle(id):
    row = get_by_id(id)
    if row:
        execute_db("UPDATE denominations SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
