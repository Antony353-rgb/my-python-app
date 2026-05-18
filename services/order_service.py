import uuid
from datetime import datetime
from database.db import query_db, execute_db
from services.voucher_service import reserve_vouchers, release_reserved_vouchers, deliver_vouchers
from services.notification_service import notify_order_delivered, notify_order_failed

def generate_order_number():
    return f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

def generate_invoice_number():
    return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def create_order(client_id, currency_id, order_type, items, created_by, fx_rate=1.0, fx_buffer=1.0):
    """
    items: list of dicts {product_id, denomination_id, supplier_id, supplier_rate_id,
                          qty, cost_price, selling_price}
    Returns order_id or None on failure.
    """
    total = sum(i["selling_price"] * i["qty"] for i in items)
    usd_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                       (client_id, currency_id), one=True)
    client = query_db("SELECT credit_enabled, credit_limit FROM clients WHERE id=?", (client_id,), one=True)
    available = (usd_row["balance"] if usd_row else 0) + (client["credit_limit"] if client and client["credit_enabled"] else 0)
    if order_type != "manual" and available < total:
        return None, "Insufficient funds"

    order_number = generate_order_number()
    invoice_number = generate_invoice_number()
    order_id = execute_db(
        """INSERT INTO orders (order_number, client_id, currency_id, order_type, total_amount,
           invoice_number, fx_rate_used, fx_buffer_pct, created_by)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (order_number, client_id, currency_id, order_type, total, invoice_number, fx_rate, fx_buffer, created_by)
    )
    for item in items:
        item_id = execute_db(
            """INSERT INTO order_items
               (order_id, product_id, denomination_id, supplier_id, supplier_rate_id,
                qty, cost_price, selling_price, total_cost, total_selling, profit)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                order_id, item["product_id"], item["denomination_id"],
                item["supplier_id"], item.get("supplier_rate_id"),
                item["qty"], item["cost_price"], item["selling_price"],
                item["cost_price"] * item["qty"],
                item["selling_price"] * item["qty"],
                (item["selling_price"] - item["cost_price"]) * item["qty"]
            )
        )
        if order_type == "api":
            reserved = reserve_vouchers(
                item["product_id"], item["denomination_id"],
                item["supplier_id"], item["qty"], item_id
            )
            if reserved:
                deliver_vouchers(item_id)
                execute_db("UPDATE order_items SET status='delivered' WHERE id=?", (item_id,))

    # Deduct client funds (not for manual orders)
    if order_type != "manual":
        bal_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                           (client_id, currency_id), one=True)
        old_bal = bal_row["balance"] if bal_row else 0
        new_bal = old_bal - total
        execute_db(
            "UPDATE client_fund_balances SET balance=?, updated_at=? WHERE client_id=? AND currency_id=?",
            (new_bal, datetime.utcnow(), client_id, currency_id)
        )
        execute_db(
            """INSERT INTO client_fund_transactions
               (client_id, currency_id, txn_type, amount, balance_before, balance_after, remarks, reference)
               VALUES (?,?,?,?,?,?,?,?)""",
            (client_id, currency_id, "order_debit", total, old_bal, new_bal, "Order placed", order_number)
        )

    # Auto-deliver API orders
    if order_type == "api":
        execute_db("UPDATE orders SET status='delivered', updated_at=? WHERE id=?", (datetime.utcnow(), order_id))

    return order_id, None

def cancel_order(order_id, cancelled_by, reason=""):
    order = query_db("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
    if not order or order["status"] == "cancelled":
        return False, "Order not found or already cancelled"
    items = query_db("SELECT * FROM order_items WHERE order_id=?", (order_id,))
    for item in items:
        release_reserved_vouchers(item["id"])
    execute_db(
        """UPDATE orders SET status='cancelled', cancelled_by=?, cancelled_at=?, cancellation_reason=?, updated_at=?
           WHERE id=?""",
        (cancelled_by, datetime.utcnow(), reason, datetime.utcnow(), order_id)
    )
    # Refund funds
    if order["order_type"] != "manual":
        bal_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                           (order["client_id"], order["currency_id"]), one=True)
        old_bal = bal_row["balance"] if bal_row else 0
        new_bal = old_bal + order["total_amount"]
        execute_db(
            "UPDATE client_fund_balances SET balance=?, updated_at=? WHERE client_id=? AND currency_id=?",
            (new_bal, datetime.utcnow(), order["client_id"], order["currency_id"])
        )
        execute_db(
            """INSERT INTO client_fund_transactions
               (client_id, currency_id, txn_type, amount, balance_before, balance_after, remarks, reference)
               VALUES (?,?,?,?,?,?,?,?)""",
            (order["client_id"], order["currency_id"], "reversal",
             order["total_amount"], old_bal, new_bal, f"Order cancelled: {reason}", order["order_number"])
        )
    return True, "Order cancelled and funds reversed"
