"""IP address utilities."""
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address
def is_valid_ip(value: str) -> bool:
    """Return whether value is a valid IPv4 or IPv6 address."""
    try: ip_address(value); return True
    except ValueError: return False
def normalize_ip(value: str) -> str:
    """Validate and normalize an IP address."""
    return str(ip_address(value))
def network_contains(network: str, address: str) -> bool:
    """Return whether address belongs to a CIDR network."""
    return ip_address(address) in ip_network(network, strict=False)
