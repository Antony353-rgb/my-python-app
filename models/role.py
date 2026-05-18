from database.db import query_db, execute_db

def get_all_roles():
    return query_db("SELECT * FROM roles ORDER BY name")

def get_role_by_id(role_id):
    return query_db("SELECT * FROM roles WHERE id=?", (role_id,), one=True)

def create_role(name):
    try:
        return execute_db("INSERT INTO roles (name) VALUES (?)", (name,))
    except Exception:
        return None

def get_permissions(role_id):
    perms = query_db("SELECT * FROM permissions WHERE role_id=?", (role_id,))
    return {p["module"]: p for p in perms}

def save_permission(role_id, module, can_view=0, can_add=0, can_edit=0, can_delete=0, can_import=0, can_export=0):
    execute_db("""INSERT INTO permissions (role_id,module,can_view,can_add,can_edit,can_delete,can_import,can_export)
                  VALUES (?,?,?,?,?,?,?,?)
                  ON CONFLICT(role_id,module) DO UPDATE SET
                  can_view=excluded.can_view, can_add=excluded.can_add, can_edit=excluded.can_edit,
                  can_delete=excluded.can_delete, can_import=excluded.can_import, can_export=excluded.can_export""",
               (role_id, module, can_view, can_add, can_edit, can_delete, can_import, can_export))

def check_permission(role_id, module, action="can_view"):
    row = query_db(f"SELECT {action} FROM permissions WHERE role_id=? AND module=?",
                   (role_id, module), one=True)
    return bool(row and row[action])
