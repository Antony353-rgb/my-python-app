from database.db import query_db, execute_db
from datetime import datetime

def get_by_id(id):
    return query_db("""SELECT o.*, c.name as client_name, cu.code as currency_code, cu.symbol
                       FROM orders o JOIN clients c ON c.id=o.client_id
                       JOIN currencies cu ON cu.id=o.currency_id WHERE o.id=?""", (id,), one=True)

def get_items(order_id):
    return query_db("""SELECT oi.*, p.name as product_name, d.label as denomination_label,
                              s.name as supplier_name
                       FROM order_items oi
                       JOIN products p ON p.id=oi.product_id
                       JOIN denominations d ON d.id=oi.denomination_id
                       JOIN suppliers s ON s.id=oi.supplier_id
                       WHERE oi.order_id=?""", (order_id,))

def get_client_orders(client_id, order_type=None, date_from=None, date_to=None):
    q = """SELECT o.*, cu.code as currency_code, cu.symbol
           FROM orders o JOIN currencies cu ON cu.id=o.currency_id WHERE o.client_id=?"""
    args = [client_id]
    if order_type: q += " AND o.order_type=?"; args.append(order_type)
    if date_from: q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    return query_db(q + " ORDER BY o.created_at DESC", args)

def get_all_orders(client_id=None, status=None, order_type=None, date_from=None, date_to=None):
    q = """SELECT o.*, c.name as client_name, cu.code as currency_code
           FROM orders o JOIN clients c ON c.id=o.client_id JOIN currencies cu ON cu.id=o.currency_id WHERE 1=1"""
    args = []
    if client_id: q += " AND o.client_id=?"; args.append(client_id)
    if status: q += " AND o.status=?"; args.append(status)
    if order_type: q += " AND o.order_type=?"; args.append(order_type)
    if date_from: q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    return query_db(q + " ORDER BY o.created_at DESC LIMIT 200", args)

def update_status(order_id, status):
    execute_db("UPDATE orders SET status=?,updated_at=? WHERE id=?", (status, datetime.utcnow(), order_id))
