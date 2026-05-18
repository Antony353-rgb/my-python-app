from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import query_db, execute_db
from utils.two_factor import verify_totp, generate_totp_secret, get_totp_uri, generate_qr_base64
from utils.auth_helpers import hash_password, is_strong_password
from utils.audit import log_action
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard_redirect"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard_redirect"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_db("SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            log_action("login_failed", "auth", record_id=None, new_value={"email": email})
            return render_template("auth/login.html")
        # Check client login enabled
        if user["user_type"] == "client":
            client = query_db("SELECT login_enabled FROM clients WHERE id=?", (user["client_id"],), one=True)
            if not client or not client["login_enabled"]:
                flash("Your account access has not been enabled. Please contact support.", "danger")
                return render_template("auth/login.html")
        # Store temp session for 2FA check
        _complete_login(user)
        return redirect(url_for("auth.dashboard_redirect"))
        session["pre_2fa_user_type"] = user["user_type"]
        if user["totp_enabled"]:
            return redirect(url_for("auth.verify_2fa"))
        if user["totp_secret"] is None and user["user_type"] != "superadmin":
            session["setup_2fa_user_id"] = user["id"]
            return redirect(url_for("auth.setup_2fa"))
        _complete_login(user)
        return redirect(url_for("auth.dashboard_redirect"))
    return render_template("auth/login.html")

# @auth_bp.route("/verify-2fa", methods=["GET", "POST"])
# def verify_2fa():
#     user_id = session.get("pre_2fa_user_id")
#     if not user_id:
#         return redirect(url_for("auth.login"))
#     user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
#     if request.method == "POST":
#         token = request.form.get("token", "").replace(" ", "")
#         if verify_totp(user["totp_secret"], token):
#             _complete_login(user)
#             session.pop("pre_2fa_user_id", None)
#             return redirect(url_for("auth.dashboard_redirect"))
#         flash("Invalid authentication code. Please try again.", "danger")
#     return render_template("auth/verify_2fa.html")

# @auth_bp.route("/setup-2fa", methods=["GET", "POST"])
# def setup_2fa():
#     user_id = session.get("setup_2fa_user_id") or session.get("user_id")
#     if not user_id:
#         return redirect(url_for("auth.login"))
#     user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
#     if not user["totp_secret"]:
#         secret = generate_totp_secret()
#         execute_db("UPDATE users SET totp_secret=? WHERE id=?", (secret, user_id))
#         user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
#     uri = get_totp_uri(user["totp_secret"], user["email"])
#     qr_b64 = generate_qr_base64(uri)
#     if request.method == "POST":
#         token = request.form.get("token", "").replace(" ", "")
#         if verify_totp(user["totp_secret"], token):
#             execute_db("UPDATE users SET totp_enabled=1 WHERE id=?", (user_id,))
#             flash("2FA setup complete! You can now login securely.", "success")
#             _complete_login(user)
#             session.pop("setup_2fa_user_id", None)
#             return redirect(url_for("auth.dashboard_redirect"))
#         flash("Invalid code. Please scan QR again and try.", "danger")
#     return render_template("auth/setup_2fa.html", qr_b64=qr_b64, secret=user["totp_secret"])

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = query_db("SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True)
        flash("If that email exists, a reset link has been sent.", "info")
        # In production: send email with reset token
    return render_template("auth/forgot_password.html")

@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        user = query_db("SELECT * FROM users WHERE id=?", (user_id,), one=True)
        if not check_password_hash(user["password_hash"], current):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html")
        if new_pw != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/change_password.html")
        ok, msg = is_strong_password(new_pw)
        if not ok:
            flash(msg, "danger")
            return render_template("auth/change_password.html")
        execute_db("UPDATE users SET password_hash=?, must_change_password=0, updated_at=? WHERE id=?",
                   (hash_password(new_pw), datetime.utcnow(), user_id))
        flash("Password changed successfully.", "success")
        log_action("password_changed", "auth", user_id)
        return redirect(url_for("auth.dashboard_redirect"))
    return render_template("auth/change_password.html")

@auth_bp.route("/logout")
def logout():
    log_action("logout", "auth")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/dashboard-redirect")
def dashboard_redirect():
    utype = session.get("user_type")
    if utype in ("superadmin", "internal"):
        return redirect(url_for("admin.dashboard"))
    elif utype == "client":
        return redirect(url_for("client.dashboard"))
    elif utype == "supplier":
        return redirect(url_for("supplier.dashboard"))
    return redirect(url_for("auth.login"))

def _complete_login(user):
    execute_db("UPDATE users SET last_login=?, last_login_ip=? WHERE id=?",
               (datetime.utcnow(), request.remote_addr, user["id"]))
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["name"]
    session["user_type"] = user["user_type"]
    session["role_id"] = user["role_id"]
    session["client_id"] = user["client_id"]
    session["supplier_id"] = user["supplier_id"]
    session["two_fa_verified"] = True
    session["must_change_password"] = bool(user["must_change_password"])
    log_action("login_success", "auth")
