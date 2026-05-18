import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/voucher_platform.db")
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit

    # Currency API
    FX_API_KEY = os.getenv("FX_API_KEY", "")
    FX_API_URL = os.getenv("FX_API_URL", "https://api.exchangerate-api.com/v4/latest/")
    DEFAULT_FX_BUFFER_PERCENT = 1.0  # 1% buffer on all FX conversions
    SYSTEM_DEFAULT_CURRENCY = "USD"

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "noreply@voucherplatform.com")
    MAIL_USE_TLS = True

    # Upload paths
    UPLOAD_FOLDER = "static/uploads"
    VOUCHER_UPLOAD_FOLDER = "static/uploads/vouchers"
    INVENTORY_UPLOAD_FOLDER = "static/uploads/inventory"
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "pdf"}

    # Supplier fund low balance threshold
    SUPPLIER_FUND_LOW_THRESHOLD = 100

    # Session timeout (seconds)
    PERMANENT_SESSION_LIFETIME = 3600
