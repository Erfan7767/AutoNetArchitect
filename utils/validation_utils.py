"""Common network input validation."""
import re
from .ip_utils import is_valid_ip
from ..constants import MIN_VLAN, MAX_VLAN, MIN_PORT, MAX_PORT
def valid_hostname(value: str) -> bool:
    """Validate a DNS-compatible hostname."""
    return bool(value and len(value) <= 253 and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", value))
def valid_ip(value: str) -> bool: """Validate an IP address."""; return is_valid_ip(value)
def valid_vlan(value: int) -> bool: """Validate a VLAN identifier."""; return MIN_VLAN <= value <= MAX_VLAN
def valid_asn(value: int) -> bool: """Validate a 32-bit ASN."""; return 1 <= value <= 4294967295
def valid_port(value: int) -> bool: """Validate a TCP/UDP port."""; return MIN_PORT <= value <= MAX_PORT
def valid_password(value: str, minimum: int = 12) -> bool: """Validate minimum password length without inspecting or logging content."""; return len(value) >= minimum and not value.isspace()
