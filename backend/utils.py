import json


def safe_div(a, b):
    """Safe division — returns 0.0 if b is zero, None, or falsy."""
    if not b:
        return 0.0
    try:
        return float(a) / float(b)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def parse_json_field(text):
    """Parse a JSON text field from SQLite. Returns dict/list or None."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
