from flask import Blueprint, render_template, session, request
from database.db import query_db
from utils.decorators import login_required, role_required

wallet_bp = Blueprint("wallet", __name__, url_prefix="/client/wallet")

@wallet_bp.route("/")
@login_required
@role_required("client")
def wallet():
    client_id = session.get("client_id")
    balances = query_db("""SELECT cfb.*, cu.code, cu.symbol, cu.name as currency_name
                           FROM client_fund_balances cfb JOIN currencies cu ON cu.id=cfb.currency_id
                           WHERE cfb.client_id=? ORDER BY cu.code""", (client_id,))
    return render_template("client/wallet.html", balances=balances)

@wallet_bp.route("/history")
@login_required
@role_required("client")
def history():
    client_id = session.get("client_id")
    currency_id = request.args.get("currency_id")
    q = """SELECT cft.*, cu.code as currency_code
           FROM client_fund_transactions cft JOIN currencies cu ON cu.id=cft.currency_id
           WHERE cft.client_id=?"""
    args = [client_id]
    if currency_id: q += " AND cft.currency_id=?"; args.append(currency_id)
    q += " ORDER BY cft.created_at DESC LIMIT 100"
    transactions = query_db(q, args)
    currencies = query_db("""SELECT cu.* FROM client_currencies cc JOIN currencies cu ON cu.id=cc.currency_id
                              WHERE cc.client_id=? ORDER BY cu.code""", (client_id,))
    return render_template("client/wallet_history.html", transactions=transactions,
                           currencies=currencies, currency_id=currency_id)
