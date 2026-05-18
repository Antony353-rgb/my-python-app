from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import query_db, execute_db
from utils.decorators import login_required, role_required
from utils.audit import log_action
from services.notification_service import notify_funds_updated, notify_low_balance
from config.settings import Config
from datetime import datetime

funds_bp = Blueprint("funds", __name__, url_prefix="/admin/funds")

@funds_bp.route("/supplier")
@login_required
@role_required("superadmin", "internal")
def supplier_funds():
    suppliers = query_db("SELECT * FROM suppliers WHERE is_active=1 ORDER BY name")
    balances = query_db("""
        SELECT sfb.*, s.name as supplier_name, cu.code as currency_code, cu.symbol
        FROM supplier_fund_balances sfb
        JOIN suppliers s ON s.id=sfb.supplier_id
        JOIN currencies cu ON cu.id=sfb.currency_id
        ORDER BY s.name, cu.code
    """)
    return render_template("admin/supplier_funds.html", balances=balances, suppliers=suppliers)

@funds_bp.route("/supplier/update", methods=["POST"])
@login_required
@role_required("superadmin")
def supplier_fund_update():
    supplier_id = request.form.get("supplier_id")
    currency_id = request.form.get("currency_id")
    balance = float(request.form.get("balance", 0))
    execute_db("""UPDATE supplier_fund_balances SET balance=?, updated_at=? WHERE supplier_id=? AND currency_id=?""",
               (balance, datetime.utcnow(), supplier_id, currency_id))
    if balance < Config.SUPPLIER_FUND_LOW_THRESHOLD:
        execute_db("UPDATE suppliers SET api_enabled=0 WHERE id=?", (supplier_id,))
        flash(f"Supplier balance below threshold — API auto-disabled.", "warning")
    log_action("update", "supplier_funds", supplier_id)
    flash("Supplier fund balance updated.", "success")
    return redirect(url_for("funds.supplier_funds"))

@funds_bp.route("/client")
@login_required
@role_required("superadmin", "internal")
def client_funds():
    clients = query_db("SELECT * FROM clients WHERE is_active=1 ORDER BY name")
    sel_client_id = request.args.get("client_id")
    balances = []
    transactions = []
    selected_client = None
    if sel_client_id:
        selected_client = query_db("SELECT * FROM clients WHERE id=?", (sel_client_id,), one=True)
        balances = query_db("""
            SELECT cfb.*, cu.code as currency_code, cu.name as currency_name, cu.symbol
            FROM client_fund_balances cfb
            JOIN currencies cu ON cu.id=cfb.currency_id
            WHERE cfb.client_id=? ORDER BY cu.code
        """, (sel_client_id,))
        transactions = query_db("""
            SELECT cft.*, cu.code as currency_code, u.name as created_by_name
            FROM client_fund_transactions cft
            JOIN currencies cu ON cu.id=cft.currency_id
            LEFT JOIN users u ON u.id=cft.created_by
            WHERE cft.client_id=?
            ORDER BY cft.created_at DESC LIMIT 50
        """, (sel_client_id,))
    return render_template("admin/client_funds.html", clients=clients, balances=balances,
                           transactions=transactions, selected_client=selected_client)

@funds_bp.route("/client/topup", methods=["POST"])
@login_required
@role_required("superadmin", "internal")
def client_topup():
    client_id = request.form.get("client_id")
    currency_id = request.form.get("currency_id")
    amount = float(request.form.get("amount", 0))
    txn_type = request.form.get("txn_type", "topup")
    remarks = request.form.get("remarks", "").strip()
    if amount <= 0:
        flash("Amount must be positive.", "danger")
        return redirect(url_for("funds.client_funds", client_id=client_id))
    bal_row = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                       (client_id, currency_id), one=True)
    old_bal = bal_row["balance"] if bal_row else 0
    if txn_type == "topup":
        new_bal = old_bal + amount
    elif txn_type == "topdown":
        new_bal = max(0, old_bal - amount)
    else:
        new_bal = old_bal
    execute_db("UPDATE client_fund_balances SET balance=?, updated_at=? WHERE client_id=? AND currency_id=?",
               (new_bal, datetime.utcnow(), client_id, currency_id))
    execute_db("""INSERT INTO client_fund_transactions (client_id, currency_id, txn_type, amount, balance_before, balance_after, remarks, created_by)
                  VALUES (?,?,?,?,?,?,?,?)""",
               (client_id, currency_id, txn_type, amount, old_bal, new_bal, remarks, session_user_id()))
    cur = query_db("SELECT code from currencies WHERE id=?", (currency_id,), one=True)
    notify_funds_updated(client_id, txn_type, amount, cur["code"] if cur else "", new_bal)
    if new_bal < 100:
        notify_low_balance(client_id, cur["code"] if cur else "", new_bal)
    log_action(txn_type, "client_funds", client_id, {"balance": old_bal}, {"balance": new_bal, "amount": amount})
    flash(f"Fund {txn_type} successful. New balance: {new_bal:.2f}", "success")
    return redirect(url_for("funds.client_funds", client_id=client_id))

@funds_bp.route("/client/swap", methods=["POST"])
@login_required
@role_required("superadmin")
def client_swap():
    client_id = request.form.get("client_id")
    from_currency_id = request.form.get("from_currency_id")
    to_currency_id = request.form.get("to_currency_id")
    amount = float(request.form.get("amount", 0))
    remarks = request.form.get("remarks", "")
    from_bal = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                        (client_id, from_currency_id), one=True)
    if not from_bal or from_bal["balance"] < amount:
        flash("Insufficient balance to swap.", "danger")
        return redirect(url_for("funds.client_funds", client_id=client_id))
    old_from = from_bal["balance"]
    new_from = old_from - amount
    execute_db("UPDATE client_fund_balances SET balance=?, updated_at=? WHERE client_id=? AND currency_id=?",
               (new_from, datetime.utcnow(), client_id, from_currency_id))
    to_bal = query_db("SELECT balance FROM client_fund_balances WHERE client_id=? AND currency_id=?",
                      (client_id, to_currency_id), one=True)
    old_to = to_bal["balance"] if to_bal else 0
    new_to = old_to + amount
    execute_db("UPDATE client_fund_balances SET balance=?, updated_at=? WHERE client_id=? AND currency_id=?",
               (new_to, datetime.utcnow(), client_id, to_currency_id))
    execute_db("""INSERT INTO client_fund_transactions (client_id, currency_id, txn_type, amount, balance_before, balance_after, remarks, created_by)
                  VALUES (?,?,?,?,?,?,?,?)""",
               (client_id, from_currency_id, "swap_out", amount, old_from, new_from, remarks, session_user_id()))
    execute_db("""INSERT INTO client_fund_transactions (client_id, currency_id, txn_type, amount, balance_before, balance_after, remarks, created_by)
                  VALUES (?,?,?,?,?,?,?,?)""",
               (client_id, to_currency_id, "swap_in", amount, old_to, new_to, remarks, session_user_id()))
    flash("Fund swap successful.", "success")
    return redirect(url_for("funds.client_funds", client_id=client_id))

def session_user_id():
    from flask import session
    return session.get("user_id")
