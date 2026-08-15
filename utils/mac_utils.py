"""MAC address parsing and normalization."""
import re
_MAC = re.compile(r"^[0-9a-fA-F]{12}$")
def normalize_mac(value: str) -> str:
    """Return a lowercase colon-separated MAC address."""
    compact = re.sub(r"[^0-9A-Fa-f]", "", value)
    if not _MAC.fullmatch(compact): raise ValueError("invalid MAC address")
    return ":".join(compact[i:i+2] for i in range(0, 12, 2)).lower()
def is_valid_mac(value: str) -> bool:
    """Return whether a MAC address can be normalized."""
    try: normalize_mac(value); return True
    except ValueError: return False
