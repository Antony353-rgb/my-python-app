"""
Supplier API Integration Service.
Handles communication with external supplier APIs.
Currently supports 1 supplier — extend for more.
"""
import requests
from database.db import query_db, execute_db
from services.notification_service import create_notification
from config.settings import Config
from datetime import datetime

class SupplierAPIError(Exception):
    pass

def get_supplier_config(supplier_id):
    return query_db(
        "SELECT * FROM suppliers WHERE id=? AND api_enabled=1 AND is_active=1",
        (supplier_id,), one=True
    )

def check_supplier_balance(supplier_id, currency_id):
    """Fetch live balance from supplier API."""
    supplier = get_supplier_config(supplier_id)
    if not supplier or not supplier["api_endpoint"]:
        return None
    try:
        resp = requests.get(
            f"{supplier['api_endpoint']}/balance",
            headers={"Authorization": f"Bearer {supplier['api_key']}"},
            timeout=10
        )
        data = resp.json()
        balance = data.get("balance", 0)
        execute_db(
            "UPDATE supplier_fund_balances SET balance=?,updated_at=? WHERE supplier_id=? AND currency_id=?",
            (balance, datetime.utcnow(), supplier_id, currency_id)
        )
        if balance < Config.SUPPLIER_FUND_LOW_THRESHOLD:
            execute_db("UPDATE suppliers SET api_enabled=0 WHERE id=?", (supplier_id,))
            _notify_admins(f"Supplier '{supplier['name']}' API disabled — balance below threshold ({balance})")
        return balance
    except Exception as e:
        print(f"[SupplierAPI] Balance check failed for supplier {supplier_id}: {e}")
        return None

def fetch_voucher_from_api(supplier_id, product_id, denomination_id, qty=1):
    """
    Call supplier API to get voucher codes on demand.
    Returns list of {'code': ..., 'pin': ...} or raises SupplierAPIError.
    """
    supplier = get_supplier_config(supplier_id)
    if not supplier:
        raise SupplierAPIError("Supplier API not enabled or not found")
    product = query_db("SELECT * FROM products WHERE id=?", (product_id,), one=True)
    denomination = query_db("SELECT * FROM denominations WHERE id=?", (denomination_id,), one=True)
    if not product or not denomination:
        raise SupplierAPIError("Product or denomination not found")
    try:
        resp = requests.post(
            f"{supplier['api_endpoint']}/order",
            json={
                "product_code": product["product_code"],
                "denomination": denomination["value"],
                "quantity": qty
            },
            headers={"Authorization": f"Bearer {supplier['api_key']}"},
            timeout=15
        )
        if resp.status_code != 200:
            raise SupplierAPIError(f"Supplier returned {resp.status_code}: {resp.text}")
        data = resp.json()
        codes = data.get("vouchers", data.get("codes", []))
        if not codes:
            raise SupplierAPIError("Supplier returned empty voucher list")
        return [{"code": c.get("code", c) if isinstance(c, dict) else c,
                 "pin": c.get("pin") if isinstance(c, dict) else None}
                for c in codes]
    except SupplierAPIError:
        raise
    except Exception as e:
        raise SupplierAPIError(f"API call failed: {e}")

def get_order_status_from_api(supplier_id, external_order_id):
    """Check status of an API order from supplier side."""
    supplier = get_supplier_config(supplier_id)
    if not supplier:
        return None
    try:
        resp = requests.get(
            f"{supplier['api_endpoint']}/order/{external_order_id}",
            headers={"Authorization": f"Bearer {supplier['api_key']}"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"[SupplierAPI] Status check failed: {e}")
        return None

def _notify_admins(message):
    admins = query_db("SELECT id FROM users WHERE user_type='superadmin' AND is_active=1")
    for admin in admins:
        create_notification(admin["id"], "system_alert", "Supplier Alert", message)
