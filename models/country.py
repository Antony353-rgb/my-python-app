from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = "SELECT * FROM countries"
    if active_only:
        q += " WHERE is_active=1"
    return query_db(q + " ORDER BY name")

def get_by_id(id):
    return query_db("SELECT * FROM countries WHERE id=?", (id,), one=True)

def create(name, code):
    return execute_db("INSERT INTO countries (name, code) VALUES (?,?)", (name, code.upper()))

def update(id, name, code):
    execute_db("UPDATE countries SET name=?, code=?, updated_at=? WHERE id=?",
               (name, code.upper(), datetime.utcnow(), id))

def toggle(id):
    row = get_by_id(id)
    if row:
        execute_db("UPDATE countries SET is_active=?, updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
