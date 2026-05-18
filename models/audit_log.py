from database.db import query_db, execute_db
import json

def log(user_id, user_email, action, module, record_id=None, old_value=None, new_value=None, ip=None, ua=None):
    execute_db("""INSERT INTO audit_logs
                  (user_id,user_email,action,module,record_id,old_value,new_value,ip_address,user_agent)
                  VALUES (?,?,?,?,?,?,?,?,?)""",
               (user_id, user_email, action, module, record_id,
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                ip, str(ua)[:200] if ua else None))

def get_logs(module=None, user_id=None, date_from=None, date_to=None, limit=500):
    q = "SELECT * FROM audit_logs WHERE 1=1"
    args = []
    if module: q += " AND module=?"; args.append(module)
    if user_id: q += " AND user_id=?"; args.append(user_id)
    if date_from: q += " AND DATE(created_at)>=?"; args.append(date_from)
    if date_to: q += " AND DATE(created_at)<=?"; args.append(date_to)
    q += f" ORDER BY created_at DESC LIMIT {limit}"
    return query_db(q, args)
