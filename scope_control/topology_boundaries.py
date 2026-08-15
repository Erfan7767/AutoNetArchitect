"""Topology boundary checks."""
class TopologyBoundaries:
    """Recognize validated topology families."""
    SUPPORTED = {"campus", "branch", "data_center", "wan"}
    def check(self, topology: str) -> dict[str, object]:
        """Return an explicit topology status."""
        return {"status": "supported" if topology in self.SUPPORTED else "unsupported", "topology": topology, "preview_available": topology not in self.SUPPORTED}
