"""Network calculation helpers."""
from ipaddress import ip_network
def usable_host_count(cidr: str) -> int:
    """Return usable host count for an IPv4 or IPv6 network."""
    network = ip_network(cidr, strict=False); count = network.num_addresses
    return max(0, count - 2) if network.version == 4 and count >= 2 else count
