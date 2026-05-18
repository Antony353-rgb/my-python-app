from werkzeug.security import generate_password_hash, check_password_hash
import re

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, hashed):
    return check_password_hash(hashed, password)

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must have at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must have at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must have at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must have at least one special character."
    return True, "OK"
