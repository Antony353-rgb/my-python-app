from database.db import query_db, execute_db
from utils.auth_helpers import hash_password
from datetime import datetime

def get_user_by_id(user_id):
    return query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)

def get_user_by_email(email):
    return query_db("SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True)

def get_all_users():
    return query_db("""SELECT u.*, r.name as role_name, c.name as client_name, s.name as supplier_name
                       FROM users u LEFT JOIN roles r ON r.id=u.role_id
                       LEFT JOIN clients c ON c.id=u.client_id
                       LEFT JOIN suppliers s ON s.id=u.supplier_id
                       ORDER BY u.user_type, u.name""")

def create_user(name, email, password, user_type, role_id=None, client_id=None, supplier_id=None):
    try:
        return execute_db(
            "INSERT INTO users (name,email,password_hash,user_type,role_id,client_id,supplier_id) VALUES (?,?,?,?,?,?,?)",
            (name, email, hash_password(password), user_type, role_id, client_id, supplier_id)
        )
    except Exception:
        return None

def update_user(user_id, **kwargs):
    kwargs['updated_at'] = datetime.utcnow()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    execute_db(f"UPDATE users SET {sets} WHERE id=?", vals)

def toggle_user(user_id):
    row = query_db("SELECT is_active FROM users WHERE id=?", (user_id,), one=True)
    if row:
        execute_db("UPDATE users SET is_active=? WHERE id=?", (1 - row["is_active"], user_id))

def update_last_login(user_id, ip):
    execute_db("UPDATE users SET last_login=?, last_login_ip=? WHERE id=?",
               (datetime.utcnow(), ip, user_id))
