from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.auth_helpers import hash_password
from utils.audit import log_action
from datetime import datetime

users_bp = Blueprint("users", __name__, url_prefix="/admin/users")

@users_bp.route("/")
@login_required
@role_required("superadmin")
def users_list():
    users = query_db("""
        SELECT u.*, r.name as role_name,
               c.name as client_name, s.name as supplier_name
        FROM users u LEFT JOIN roles r ON r.id=u.role_id
        LEFT JOIN clients c ON c.id=u.client_id
        LEFT JOIN suppliers s ON s.id=u.supplier_id
        ORDER BY u.user_type, u.name
    """)
    roles = query_db("SELECT * FROM roles ORDER BY name")
    clients = query_db("SELECT id, name FROM clients WHERE is_active=1 ORDER BY name")
    suppliers = query_db("SELECT id, name FROM suppliers WHERE is_active=1 ORDER BY name")
    return render_template("admin/users_list.html", users=users, roles=roles,
                           clients=clients, suppliers=suppliers)

@users_bp.route("/save", methods=["POST"])
@login_required
@role_required("superadmin")
def user_save():
    id_ = request.form.get("id")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    user_type = request.form.get("user_type")
    role_id = request.form.get("role_id") or None
    client_id = request.form.get("client_id") or None
    supplier_id = request.form.get("supplier_id") or None
    password = request.form.get("password", "")
    if not name or not email:
        flash("Name and email required.", "danger")
        return redirect(url_for("users.users_list"))
    if id_:
        execute_db("""UPDATE users SET name=?, email=?, user_type=?, role_id=?, client_id=?, supplier_id=?, updated_at=?
                      WHERE id=?""", (name, email, user_type, role_id, client_id, supplier_id, datetime.utcnow(), id_))
        if password:
            execute_db("UPDATE users SET password_hash=?, must_change_password=1 WHERE id=?",
                       (hash_password(password), id_))
        flash("User updated.", "success")
    else:
        if not password:
            flash("Password required for new user.", "danger")
            return redirect(url_for("users.users_list"))
        try:
            execute_db("""INSERT INTO users (name, email, password_hash, user_type, role_id, client_id, supplier_id)
                          VALUES (?,?,?,?,?,?,?)""",
                       (name, email, hash_password(password), user_type, role_id, client_id, supplier_id))
            flash("User created.", "success")
        except Exception:
            flash("Email already exists.", "danger")
    log_action("save", "users", id_)
    return redirect(url_for("users.users_list"))

@users_bp.route("/toggle/<int:id>")
@login_required
@role_required("superadmin")
def user_toggle(id):
    row = query_db("SELECT is_active FROM users WHERE id=?", (id,), one=True)
    execute_db("UPDATE users SET is_active=?, updated_at=? WHERE id=?", (1 - row["is_active"], datetime.utcnow(), id))
    flash("User status updated.", "success")
    return redirect(url_for("users.users_list"))

@users_bp.route("/reset-password/<int:id>", methods=["POST"])
@login_required
@role_required("superadmin")
def reset_password(id):
    new_pw = request.form.get("new_password", "")
    if not new_pw:
        flash("Password required.", "danger")
        return redirect(url_for("users.users_list"))
    execute_db("UPDATE users SET password_hash=?, must_change_password=1, updated_at=? WHERE id=?",
               (hash_password(new_pw), datetime.utcnow(), id))
    log_action("reset_password", "users", id)
    flash("Password reset. User will be prompted to change on next login.", "success")
    return redirect(url_for("users.users_list"))

@users_bp.route("/roles")
@login_required
@role_required("superadmin")
def roles_list():
    roles = query_db("SELECT * FROM roles ORDER BY name")
    modules = ["masters", "catalogue", "clients", "suppliers", "orders", "inventory", "reports", "users", "funds"]
    role_perms = {}
    for r in roles:
        perms = query_db("SELECT * FROM permissions WHERE role_id=?", (r["id"],))
        role_perms[r["id"]] = {p["module"]: p for p in perms}
    return render_template("admin/roles_list.html", roles=roles, modules=modules, role_perms=role_perms)

@users_bp.route("/roles/save", methods=["POST"])
@login_required
@role_required("superadmin")
def role_save():
    role_name = request.form.get("role_name", "").strip()
    if role_name:
        try:
            execute_db("INSERT INTO roles (name) VALUES (?)", (role_name,))
            flash("Role created.", "success")
        except Exception:
            flash("Role name already exists.", "danger")
    return redirect(url_for("users.roles_list"))

@users_bp.route("/roles/<int:role_id>/permissions", methods=["POST"])
@login_required
@role_required("superadmin")
def save_permissions(role_id):
    modules = ["masters", "catalogue", "clients", "suppliers", "orders", "inventory", "reports", "users", "funds"]
    for m in modules:
        execute_db("""INSERT INTO permissions (role_id, module, can_view, can_add, can_edit, can_delete, can_import, can_export)
                      VALUES (?,?,?,?,?,?,?,?)
                      ON CONFLICT(role_id, module) DO UPDATE SET
                      can_view=excluded.can_view, can_add=excluded.can_add, can_edit=excluded.can_edit,
                      can_delete=excluded.can_delete, can_import=excluded.can_import, can_export=excluded.can_export""",
                   (role_id, m,
                    1 if request.form.get(f"{m}_view") else 0,
                    1 if request.form.get(f"{m}_add") else 0,
                    1 if request.form.get(f"{m}_edit") else 0,
                    1 if request.form.get(f"{m}_delete") else 0,
                    1 if request.form.get(f"{m}_import") else 0,
                    1 if request.form.get(f"{m}_export") else 0))
    flash("Permissions saved.", "success")
    return redirect(url_for("users.roles_list"))

@users_bp.route("/audit-trail")
@login_required
@role_required("superadmin", "internal")
def audit_trail():
    module = request.args.get("module")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = "SELECT * FROM audit_logs WHERE 1=1"
    args = []
    if module: q += " AND module=?"; args.append(module)
    if date_from: q += " AND DATE(created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(created_at)<=?"; args.append(date_to)
    q += " ORDER BY created_at DESC LIMIT 500"
    logs = query_db(q, args)
    return render_template("admin/audit_trail.html", logs=logs,
                           filters={"module": module, "date_from": date_from, "date_to": date_to})
