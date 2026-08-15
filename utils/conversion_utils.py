"""Data conversion utilities."""
import json
def to_json(value: object) -> str: """Serialize a value to stable JSON."""; return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
def parse_bool(value: object) -> bool:
    """Parse common boolean representations."""
    if isinstance(value, bool): return value
    if str(value).lower() in {"true", "1", "yes", "on"}: return True
    if str(value).lower() in {"false", "0", "no", "off"}: return False
    raise ValueError("invalid boolean")
