import requests
from datetime import datetime, timedelta
from database.db import query_db, execute_db
from config.settings import Config

def fetch_live_rate(from_currency, to_currency):
    """Fetch from API or fallback to cached DB rate."""
    if from_currency == to_currency:
        return 1.0
    try:
        url = f"{Config.FX_API_URL}{from_currency}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        rate = data.get("rates", {}).get(to_currency)
        if rate:
            execute_db(
                """INSERT INTO fx_rates (from_currency, to_currency, rate, fetched_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(from_currency, to_currency) DO UPDATE SET rate=excluded.rate, fetched_at=excluded.fetched_at""",
                (from_currency, to_currency, rate, datetime.utcnow())
            )
            return rate
    except Exception as e:
        print(f"FX API error: {e}")
    # Fallback to cached
    cached = query_db(
        "SELECT rate FROM fx_rates WHERE from_currency=? AND to_currency=?",
        (from_currency, to_currency), one=True
    )
    return cached["rate"] if cached else None

def convert_amount(amount, from_currency, to_currency, buffer_pct=None):
    """Convert amount and apply buffer."""
    if from_currency == to_currency:
        return amount, 1.0
    rate = fetch_live_rate(from_currency, to_currency)
    if not rate:
        return None, None
    buf = buffer_pct if buffer_pct is not None else Config.DEFAULT_FX_BUFFER_PERCENT
    effective_rate = rate * (1 + buf / 100)
    return round(amount * effective_rate, 4), effective_rate

def get_cached_rate(from_currency, to_currency):
    row = query_db(
        "SELECT rate, fetched_at FROM fx_rates WHERE from_currency=? AND to_currency=?",
        (from_currency, to_currency), one=True
    )
    return row
