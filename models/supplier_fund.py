from database.db import query_db, execute_db
from datetime import datetime
from config.settings import Config

def get_all_balances():
    return query_db("""SELECT sfb.*, s.name as supplier_name, s.api_enabled,
                              cu.code as currency_code, cu.symbol
                       FROM supplier_fund_balances sfb
                       JOIN suppliers s ON s.id=sfb.supplier_id
                       JOIN currencies cu ON cu.id=sfb.currency_id
                       ORDER BY s.name, cu.code""")

def get_balance(supplier_id, currency_id):
    return query_db("SELECT balance FROM supplier_fund_balances WHERE supplier_id=? AND currency_id=?",
                    (supplier_id, currency_id), one=True)

def update_balance(supplier_id, currency_id, balance):
    execute_db("UPDATE supplier_fund_balances SET balance=?,updated_at=? WHERE supplier_id=? AND currency_id=?",
               (balance, datetime.utcnow(), supplier_id, currency_id))
    if balance < Config.SUPPLIER_FUND_LOW_THRESHOLD:
        execute_db("UPDATE suppliers SET api_enabled=0 WHERE id=?", (supplier_id,))
        return False  # signals API was disabled
    return True
