import sqlite3
import os
from config.settings import Config

def get_db():
    import os
    import shutil
    db_path = Config.DATABASE_PATH

    if os.environ.get("VERCEL"):
        tmp_db = "/tmp/vercel_demo.db"
        if not os.path.exists(tmp_db):
            actual_db_path = os.path.abspath(db_path)
            if os.path.exists(actual_db_path):
                shutil.copy2(actual_db_path, tmp_db)
            else:
                # Create a 0-byte file first to prevent recursion during init_db and seed
                open(tmp_db, "w").close()
                init_db()
                from database.seed_data import seed
                seed()
        conn = sqlite3.connect(tmp_db)
    else:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialised.")

def query_db(query, args=(), one=False):
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=()):
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def execute_many_db(query, args_list):
    conn = get_db()
    try:
        conn.executemany(query, args_list)
        conn.commit()
    finally:
        conn.close()
