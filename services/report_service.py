from database.db import query_db

def funding_report(client_id=None, date_from=None, date_to=None):
    q = """SELECT cft.*, c.name as client_name, cu.code as currency_code, u.name as created_by_name
           FROM client_fund_transactions cft
           JOIN clients c ON c.id = cft.client_id
           JOIN currencies cu ON cu.id = cft.currency_id
           LEFT JOIN users u ON u.id = cft.created_by
           WHERE 1=1"""
    args = []
    if client_id:
        q += " AND cft.client_id=?"; args.append(client_id)
    if date_from:
        q += " AND DATE(cft.created_at)>=?"; args.append(date_from)
    if date_to:
        q += " AND DATE(cft.created_at)<=?"; args.append(date_to)
    q += " ORDER BY cft.created_at DESC"
    return query_db(q, args)

def client_productivity_report(client_id=None, date_from=None, date_to=None):
    q = """SELECT c.name as client_name, b.name as brand, co.name as country,
                  p.name as product, d.label as denomination, cu.code as currency,
                  COUNT(oi.id) as total_orders, SUM(oi.qty) as total_qty,
                  SUM(oi.total_selling) as total_revenue, SUM(oi.profit) as total_profit
           FROM order_items oi
           JOIN orders o ON o.id = oi.order_id
           JOIN clients c ON c.id = o.client_id
           JOIN products p ON p.id = oi.product_id
           JOIN brands b ON b.id = p.brand_id
           JOIN countries co ON co.id = p.country_id
           JOIN currencies cu ON cu.id = p.currency_id
           JOIN denominations d ON d.id = oi.denomination_id
           WHERE o.status != 'cancelled'"""
    args = []
    if client_id:
        q += " AND o.client_id=?"; args.append(client_id)
    if date_from:
        q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to:
        q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    q += " GROUP BY c.id, b.id, co.id, p.id, d.id ORDER BY total_revenue DESC"
    return query_db(q, args)

def supplier_productivity_report(supplier_id=None, date_from=None, date_to=None):
    q = """SELECT s.name as supplier_name, b.name as brand, co.name as country,
                  p.name as product, d.label as denomination,
                  SUM(oi.qty) as total_qty, SUM(oi.total_cost) as total_cost,
                  SUM(oi.total_selling) as total_selling, SUM(oi.profit) as total_profit
           FROM order_items oi
           JOIN orders o ON o.id = oi.order_id
           JOIN suppliers s ON s.id = oi.supplier_id
           JOIN products p ON p.id = oi.product_id
           JOIN brands b ON b.id = p.brand_id
           JOIN countries co ON co.id = p.country_id
           JOIN denominations d ON d.id = oi.denomination_id
           WHERE o.status != 'cancelled'"""
    args = []
    if supplier_id:
        q += " AND oi.supplier_id=?"; args.append(supplier_id)
    if date_from:
        q += " AND DATE(o.created_at)>=?"; args.append(date_from)
    if date_to:
        q += " AND DATE(o.created_at)<=?"; args.append(date_to)
    q += " GROUP BY s.id, b.id, co.id, p.id, d.id ORDER BY total_selling DESC"
    return query_db(q, args)
