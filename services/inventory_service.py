from database.db import query_db, execute_db
from datetime import datetime

def create_inventory_order(supplier_id, product_id, denomination_id, qty, cost_price,
                           rate_type=None, rate_value=None, lpo_number=None, remarks=None, created_by=None):
    total_cost = qty * cost_price
    return execute_db(
        """INSERT INTO inventory_orders
           (supplier_id, product_id, denomination_id, qty_ordered, cost_price, rate_type,
            rate_value, total_cost, lpo_number, remarks, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (supplier_id, product_id, denomination_id, qty, cost_price, rate_type,
         rate_value, total_cost, lpo_number, remarks, created_by)
    )

def record_inventory_delivery(inv_order_id, qty_delivered, codes):
    """codes: list of {'code': ..., 'pin': ..., 'expiry_date': ...}"""
    from services.voucher_service import bulk_upload_codes
    order = query_db("SELECT * FROM inventory_orders WHERE id=?", (inv_order_id,), one=True)
    if not order:
        return False, "Inventory order not found"
    new_delivered = order["qty_delivered"] + qty_delivered
    status = "delivered" if new_delivered >= order["qty_ordered"] else "partial"
    execute_db(
        "UPDATE inventory_orders SET qty_delivered=?, status=?, updated_at=? WHERE id=?",
        (new_delivered, status, datetime.utcnow(), inv_order_id)
    )
    if codes:
        bulk_upload_codes(order["product_id"], order["denomination_id"],
                          order["supplier_id"], codes, order["cost_price"])
    return True, f"Delivery recorded. Status: {status}"

def get_inventory_balance():
    return query_db(
        """SELECT p.name as product_name, b.name as brand_name, c.name as country_name,
                  d.label as denomination, cu.code as currency, s.name as supplier_name,
                  COUNT(CASE WHEN vc.status='available' THEN 1 END) as available,
                  COUNT(CASE WHEN vc.status='reserved' THEN 1 END) as reserved,
                  COUNT(CASE WHEN vc.status='sold' THEN 1 END) as sold,
                  COUNT(CASE WHEN vc.status='expired' THEN 1 END) as expired
           FROM voucher_codes vc
           JOIN products p ON p.id = vc.product_id
           JOIN brands b ON b.id = p.brand_id
           JOIN countries c ON c.id = p.country_id
           JOIN currencies cu ON cu.id = p.currency_id
           JOIN denominations d ON d.id = vc.denomination_id
           JOIN suppliers s ON s.id = vc.supplier_id
           GROUP BY p.id, d.id, s.id"""
    )
