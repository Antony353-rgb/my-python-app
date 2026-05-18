from database.db import query_db, execute_db
from datetime import datetime

def get_all(active_only=False):
    q = """SELECT b.*, GROUP_CONCAT(c.name, ', ') as countries
           FROM brands b
           LEFT JOIN brand_countries bc ON bc.brand_id=b.id
           LEFT JOIN countries c ON c.id=bc.country_id"""
    if active_only:
        q += " WHERE b.is_active=1"
    return query_db(q + " GROUP BY b.id ORDER BY b.name")

def get_by_id(id):
    return query_db("SELECT * FROM brands WHERE id=?", (id,), one=True)

def create(name, country_ids=None):
    bid = execute_db("INSERT INTO brands (name) VALUES (?)", (name,))
    if country_ids:
        for cid in country_ids:
            try:
                execute_db("INSERT INTO brand_countries (brand_id,country_id) VALUES (?,?)", (bid, cid))
            except Exception:
                pass
    return bid

def update(id, name, country_ids=None):
    execute_db("UPDATE brands SET name=?,updated_at=? WHERE id=?", (name, datetime.utcnow(), id))
    if country_ids is not None:
        execute_db("DELETE FROM brand_countries WHERE brand_id=?", (id,))
        for cid in country_ids:
            try:
                execute_db("INSERT INTO brand_countries (brand_id,country_id) VALUES (?,?)", (id, cid))
            except Exception:
                pass

def toggle(id):
    row = get_by_id(id)
    if row:
        execute_db("UPDATE brands SET is_active=?,updated_at=? WHERE id=?",
                   (1 - row["is_active"], datetime.utcnow(), id))
