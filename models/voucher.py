from database.db import query_db, execute_db
from datetime import datetime

def get_available_count(product_id, denomination_id, supplier_id):
    row = query_db("""SELECT COUNT(*) as cnt FROM voucher_codes
                      WHERE product_id=? AND denomination_id=? AND supplier_id=? AND status='available'""",
                   (product_id, denomination_id, supplier_id), one=True)
    return row["cnt"] if row else 0

def get_codes_for_order_item(order_item_id):
    return query_db("SELECT code, pin, expiry_date FROM voucher_codes WHERE order_item_id=? AND status='sold'",
                    (order_item_id,))

def expire_old_codes():
    execute_db("""UPDATE voucher_codes SET status='expired'
                  WHERE status='available' AND expiry_date IS NOT NULL AND expiry_date < DATE('now')""")
