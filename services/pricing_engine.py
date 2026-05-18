from database.db import query_db
from services.fx_service import convert_amount

def calculate_selling_price(base_price, rate_type, rate_value):
    """Apply markup or discount to base price."""
    if rate_type == "discount_pct":
        return round(base_price * (1 - rate_value / 100), 4)
    elif rate_type == "markup_pct":
        return round(base_price * (1 + rate_value / 100), 4)
    elif rate_type == "discount_amt":
        return round(base_price - rate_value, 4)
    elif rate_type == "markup_amt":
        return round(base_price + rate_value, 4)
    elif rate_type == "fixed":
        return round(rate_value, 4)
    return base_price

def get_best_supplier_rate(product_id, denomination_id, search_currency_code, client_fx_buffer):
    """
    Pick the lowest cost supplier for a product.
    Returns list of dicts sorted by cost in search_currency.
    """
    rates = query_db(
        """SELECT sr.*, s.name as supplier_name, s.id as supplier_id,
                  d.type as denom_type, d.value as denom_value,
                  c.code as brand_currency_code
           FROM supplier_rates sr
           JOIN suppliers s ON s.id = sr.supplier_id
           JOIN products p ON p.id = sr.product_id
           JOIN currencies c ON c.id = p.currency_id
           JOIN denominations d ON d.id = sr.denomination_id
           WHERE sr.product_id=? AND sr.denomination_id=? AND sr.is_active=1 AND s.is_active=1
           ORDER BY sr.rate_value ASC""",
        (product_id, denomination_id)
    )
    results = []
    for r in rates:
        base = r["cost_price"] if r["cost_price"] else r["denom_value"]
        cost = calculate_selling_price(base, r["rate_type"], r["rate_value"])
        converted, fx_rate = convert_amount(cost, r["brand_currency_code"], search_currency_code, client_fx_buffer)
        if converted is not None:
            stock = query_db(
                """SELECT COUNT(*) as cnt FROM voucher_codes
                   WHERE product_id=? AND denomination_id=? AND supplier_id=? AND status='available'""",
                (product_id, denomination_id, r["supplier_id"]), one=True
            )
            results.append({
                "supplier_id": r["supplier_id"],
                "supplier_name": r["supplier_name"],
                "supplier_rate_id": r["id"],
                "cost_price_original": cost,
                "cost_price_converted": converted,
                "fx_rate": fx_rate,
                "stock_count": stock["cnt"] if stock else 0,
                "rate_type": r["rate_type"],
                "rate_value": r["rate_value"],
            })
    results.sort(key=lambda x: x["cost_price_converted"])
    return results

def get_client_selling_price(cost_price, catalogue_product, min_markup_pct):
    """Apply client catalogue pricing on top of supplier cost."""
    selling = calculate_selling_price(
        cost_price,
        catalogue_product["client_rate_type"],
        catalogue_product["client_rate_value"]
    )
    # Enforce minimum markup
    min_price = cost_price * (1 + min_markup_pct / 100)
    if selling < min_price:
        selling = min_price
    return round(selling, 4)
