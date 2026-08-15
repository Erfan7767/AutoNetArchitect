"""Scale boundary checks."""
class ScaleBoundaries:
    """Validated scale classes."""
    LIMITS = {"small": 50, "medium": 250, "large": 500}
    def classify(self, devices: int) -> str:
        """Classify device count or return unsupported."""
        if devices < 0: raise ValueError("device count cannot be negative")
        for name, limit in self.LIMITS.items():
            if devices <= limit: return name
        return "unsupported"
    def allowed(self, devices: int) -> bool: """Return whether device count is in validated scope."""; return self.classify(devices) != "unsupported"
