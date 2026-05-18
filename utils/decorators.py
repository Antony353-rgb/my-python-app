from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from database.db import query_db

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def role_required(*allowed_types):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("user_type") not in allowed_types:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

def permission_required(module, action="can_view"):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("user_type") == "superadmin":
                return f(*args, **kwargs)
            role_id = session.get("role_id")
            if not role_id:
                abort(403)
            perm = query_db(
                f"SELECT {action} FROM permissions WHERE role_id=? AND module=?",
                (role_id, module), one=True
            )
            if not perm or not perm[action]:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

def two_fa_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("two_fa_verified"):
            return redirect(url_for("auth.verify_2fa"))
        return f(*args, **kwargs)
    return decorated
