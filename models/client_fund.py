from database.db import query_db, execute_db
from datetime import datetime

def get_balances(client_id):
    return query_db("""SELECT cfb.*, cu.code, cu.name as currency_name, cu.symbol
                       FROM client_fund_balances cfb
                       JOIN currencies cu ON cu.id=cfb.currency_id
                       WHERE cfb.client_id=? ORDER BY cu.code""", (client_id,))

def get_balance(client_id, currency_id):
    row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                   (client_id, currency_id), one=True)
    return row["balance"] if row else 0.0

def add_transaction(client_id, currency_id, txn_type, amount, remarks=None, created_by=None, reference=None):
    old_bal = get_balance(client_id, currency_id)
    if txn_type in ("topup", "swap_in", "reversal"):
        new_bal = old_bal + amount
    elif txn_type in ("topdown", "swap_out", "order_debit"):
        new_bal = max(0, old_bal - amount)
    else:
        new_bal = old_bal
    execute_db("UPDATE client_fund_balances SET balance=?,updated_at=? WHERE client_id=? AND currency_id=?",
               (new_bal, datetime.utcnow(), client_id, currency_id))
    execute_db("""INSERT INTO client_fund_transactions
                  (client_id,currency_id,txn_type,amount,balance_before,balance_after,remarks,created_by,reference)
                  VALUES (?,?,?,?,?,?,?,?,?)""",
               (client_id, currency_id, txn_type, amount, old_bal, new_bal, remarks, created_by, reference))
    return old_bal, new_bal

def get_transactions(client_id, currency_id=None, limit=100):
    q = """SELECT cft.*, cu.code as currency_code FROM client_fund_transactions cft
           JOIN currencies cu ON cu.id=cft.currency_id WHERE cft.client_id=?"""
    args = [client_id]
    if currency_id:
        q += " AND cft.currency_id=?"; args.append(currency_id)
    q += " ORDER BY cft.created_at DESC LIMIT ?"
    args.append(limit)
    return query_db(q, args)
