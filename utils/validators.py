import re

def is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def is_valid_phone(phone):
    return bool(re.match(r"^\+?[\d\s\-]{7,15}$", phone))

def sanitize_string(s, max_length=255):
    if not s:
        return ""
    return str(s).strip()[:max_length]
