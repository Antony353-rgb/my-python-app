from database.db import execute_db, query_db
from datetime import datetime

def create_notification(user_id, notif_type, title, message):
    execute_db(
        "INSERT INTO notifications (user_id, type, title, message) VALUES (?,?,?,?)",
        (user_id, notif_type, title, message)
    )

def notify_order_delivered(order_id):
    order = query_db("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
    if not order:
        return
    users = query_db("SELECT id FROM users WHERE client_id=?", (order["client_id"],))
    for u in users:
        create_notification(u["id"], "order_delivered", "Order Delivered",
                            f"Your order {order['order_number']} has been delivered.")

def notify_order_failed(order_id, reason):
    order = query_db("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
    if not order:
        return
    users = query_db("SELECT id FROM users WHERE client_id=?", (order["client_id"],))
    for u in users:
        create_notification(u["id"], "order_failed", "Order Failed",
                            f"Order {order['order_number']} failed. Reason: {reason}")

def notify_funds_updated(client_id, txn_type, amount, currency_code, new_balance):
    users = query_db("SELECT id FROM users WHERE client_id=?", (client_id,))
    for u in users:
        verb = "topped up" if txn_type == "topup" else "adjusted"
        create_notification(u["id"], "funds_updated", f"Funds {verb.title()}",
                            f"Your {currency_code} balance was {verb} by {amount:.2f}. New balance: {new_balance:.2f} {currency_code}")

def notify_low_balance(client_id, currency_code, balance):
    users = query_db("SELECT id FROM users WHERE client_id=?", (client_id,))
    for u in users:
        create_notification(u["id"], "low_balance", "Low Balance Warning",
                            f"Your {currency_code} balance is low: {balance:.2f} {currency_code}. Please topup to continue ordering.")

def get_user_notifications(user_id, unread_only=False):
    if unread_only:
        return query_db("SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC", (user_id,))
    return query_db("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (user_id,))

def mark_all_read(user_id):
    execute_db("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
