from database.db import query_db, execute_db
from datetime import datetime

def get_rate(from_currency, to_currency):
    return query_db("SELECT * FROM fx_rates WHERE from_currency=? AND to_currency=?",
                    (from_currency, to_currency), one=True)

def upsert_rate(from_currency, to_currency, rate):
    execute_db("""INSERT INTO fx_rates (from_currency,to_currency,rate,fetched_at)
                  VALUES (?,?,?,?)
                  ON CONFLICT(from_currency,to_currency) DO UPDATE SET rate=excluded.rate, fetched_at=excluded.fetched_at""",
               (from_currency, to_currency, rate, datetime.utcnow()))

def get_all_rates():
    return query_db("SELECT * FROM fx_rates ORDER BY from_currency, to_currency")
