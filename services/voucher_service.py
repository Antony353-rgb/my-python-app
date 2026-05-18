from database.db import query_db, execute_db, execute_many_db
from datetime import datetime

def get_available_stock(product_id, denomination_id, supplier_id):
    row = query_db(
        """SELECT COUNT(*) as cnt FROM voucher_codes
           WHERE product_id=? AND denomination_id=? AND supplier_id=? AND status='available'""",
        (product_id, denomination_id, supplier_id), one=True
    )
    return row["cnt"] if row else 0

def reserve_vouchers(product_id, denomination_id, supplier_id, qty, order_item_id):
    codes = query_db(
        """SELECT id FROM voucher_codes
           WHERE product_id=? AND denomination_id=? AND supplier_id=? AND status='available'
           LIMIT ?""",
        (product_id, denomination_id, supplier_id, qty)
    )
    if len(codes) < qty:
        return False
    ids = tuple(c["id"] for c in codes)
    placeholders = ",".join("?" * len(ids))
    execute_db(
        f"""UPDATE voucher_codes SET status='reserved', order_item_id=?, reserved_at=?
            WHERE id IN ({placeholders})""",
        (order_item_id, datetime.utcnow(), *ids)
    )
    return True

def deliver_vouchers(order_item_id):
    execute_db(
        "UPDATE voucher_codes SET status='sold', sold_at=? WHERE order_item_id=?",
        (datetime.utcnow(), order_item_id)
    )

def release_reserved_vouchers(order_item_id):
    execute_db(
        "UPDATE voucher_codes SET status='available', order_item_id=NULL, reserved_at=NULL WHERE order_item_id=?",
        (order_item_id,)
    )

def get_order_codes(order_item_id):
    return query_db(
        "SELECT code, pin, expiry_date FROM voucher_codes WHERE order_item_id=? AND status='sold'",
        (order_item_id,)
    )

def bulk_upload_codes(product_id, denomination_id, supplier_id, codes_list, cost_price):
    """codes_list: list of dicts with keys: code, pin (opt), expiry_date (opt)"""
    data = [
        (product_id, denomination_id, supplier_id, c.get("code"), c.get("pin"), cost_price, c.get("expiry_date"))
        for c in codes_list
    ]
    execute_many_db(
        """INSERT OR IGNORE INTO voucher_codes
           (product_id, denomination_id, supplier_id, code, pin, cost_price, expiry_date)
           VALUES (?,?,?,?,?,?,?)""",
        data
    )
    return len(data)
