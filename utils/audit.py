import json
from flask import session, request
from database.db import execute_db

def log_action(action, module, record_id=None, old_value=None, new_value=None):
    try:
        execute_db(
            """INSERT INTO audit_logs
               (user_id, user_email, action, module, record_id, old_value, new_value, ip_address, user_agent)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                session.get("user_id"),
                session.get("user_email"),
                action,
                module,
                record_id,
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                request.remote_addr,
                request.headers.get("User-Agent", "")[:200],
            )
        )
    except Exception as e:
        print(f"Audit log error: {e}")
