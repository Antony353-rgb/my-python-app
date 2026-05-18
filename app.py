from flask import Flask, render_template, session
from flask_wtf.csrf import CSRFProtect
from config.settings import Config
from database.db import init_db
import os

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)

    import os
    is_vercel = os.environ.get("VERCEL")

    session_dir = "/tmp/flask_session" if is_vercel else "flask_session"
    os.makedirs(session_dir, exist_ok=True)
    app.config['SESSION_FILE_DIR'] = session_dir

    # Vercel-க்காக Upload ஃபோல்டர்களையும் /tmp க்கு மாற்றுதல்
    if is_vercel:
        Config.UPLOAD_FOLDER = "/tmp/uploads"
        Config.VOUCHER_UPLOAD_FOLDER = "/tmp/vouchers"
        Config.INVENTORY_UPLOAD_FOLDER = "/tmp/inventory"

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.VOUCHER_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.INVENTORY_UPLOAD_FOLDER, exist_ok=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.admin_masters import masters_bp
    from routes.admin_catalogue import catalogue_bp
    from routes.admin_orders import orders_admin_bp
    from routes.admin_inventory import inventory_bp
    from routes.admin_reports import reports_bp
    from routes.admin_users import users_bp
    from routes.admin_funds import funds_bp
    from routes.client import client_bp
    from routes.client_orders import client_orders_bp
    from routes.client_wallet import wallet_bp
    from routes.supplier import supplier_bp
    from routes.supplier_inventory import supplier_inv_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(masters_bp)
    app.register_blueprint(catalogue_bp)
    app.register_blueprint(orders_admin_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(funds_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(client_orders_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(supplier_inv_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # Context processors
    @app.context_processor
    def inject_globals():
        from services.notification_service import get_user_notifications
        unread = 0
        if session.get("user_id"):
            unread = len(get_user_notifications(session["user_id"], unread_only=True))
        return {"unread_notifications": unread, "session": session}

    return app

app = create_app()
