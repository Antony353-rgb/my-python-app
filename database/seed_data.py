"""
Run this once after init_db() to populate default data.
python -c "from database.seed_data import seed; seed()"
"""
from database.db import execute_db, query_db
from werkzeug.security import generate_password_hash
import pyotp

def seed():
    # Default roles
    roles = [
        ("superadmin",),
        ("internal_staff",),
        ("client_user",),
        ("supplier_user",),
    ]
    for r in roles:
        try:
            execute_db("INSERT INTO roles (name) VALUES (?)", r)
        except Exception:
            pass

    # Default currencies
    currencies = [
        ("US Dollar", "USD", "$"),
        ("Euro", "EUR", "€"),
        ("British Pound", "GBP", "£"),
        ("Indian Rupee", "INR", "₹"),
        ("UAE Dirham", "AED", "د.إ"),
        ("Saudi Riyal", "SAR", "﷼"),
    ]
    for c in currencies:
        try:
            execute_db("INSERT INTO currencies (name, code, symbol) VALUES (?,?,?)", c)
        except Exception:
            pass

    # Default countries
    countries = [
        ("United States", "US"),
        ("United Kingdom", "GB"),
        ("India", "IN"),
        ("United Arab Emirates", "AE"),
        ("Saudi Arabia", "SA"),
        ("Germany", "DE"),
        ("France", "FR"),
    ]
    for c in countries:
        try:
            execute_db("INSERT INTO countries (name, code) VALUES (?,?)", c)
        except Exception:
            pass

    # Superadmin user
    existing = query_db("SELECT id FROM users WHERE email=?", ("admin@platform.com",), one=True)
    if not existing:
        superadmin_role = query_db("SELECT id FROM roles WHERE name='superadmin'", one=True)
        execute_db(
            """INSERT INTO users (name, email, password_hash, user_type, role_id, must_change_password)
               VALUES (?,?,?,?,?,?)""",
            (
                "Super Admin",
                "admin@platform.com",
                generate_password_hash("Admin@1234"),
                "superadmin",
                superadmin_role["id"] if superadmin_role else 1,
                0,
            )
        )
        print("Superadmin created: admin@platform.com / Admin@1234")

    print("Seed data inserted.")

if __name__ == "__main__":
    seed()
