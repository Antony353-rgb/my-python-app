from database.db import query_db, execute_db

def create(user_id, type_, title, message):
    execute_db("INSERT INTO notifications (user_id,type,title,message) VALUES (?,?,?,?)",
               (user_id, type_, title, message))

def get_for_user(user_id, unread_only=False, limit=50):
    q = "SELECT * FROM notifications WHERE user_id=?"
    args = [user_id]
    if unread_only:
        q += " AND is_read=0"
    q += f" ORDER BY created_at DESC LIMIT {limit}"
    return query_db(q, args)

def mark_read(user_id):
    execute_db("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))

def unread_count(user_id):
    row = query_db("SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0", (user_id,), one=True)
    return row["cnt"] if row else 0
