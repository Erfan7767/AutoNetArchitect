"""Protocol combination boundary checks."""
class ProtocolBoundaries:
    """Allow only explicitly validated protocol combinations."""
    SUPPORTED = {frozenset({"ospf"}), frozenset({"bgp"}), frozenset({"ospf", "vlan"}), frozenset({"bgp", "mpls"})}
    def check(self, protocols: set[str]) -> dict[str, object]:
        """Return supported or explicit unsupported status."""
        return {"status": "supported" if frozenset(protocols) in self.SUPPORTED else "unsupported", "protocols": sorted(protocols)}
