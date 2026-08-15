"""Decision-type confidence thresholds."""
class ConfidenceGovernor:
    """Enforce minimum confidence by decision risk."""
    THRESHOLDS = {"architecture": 0.75, "vendor_selection": 0.8, "deployment": 0.9, "low_risk": 0.6}
    def threshold(self, decision_type: str) -> float:
        """Return the configured threshold."""
        return self.THRESHOLDS.get(decision_type, 0.75)
    def allow(self, decision_type: str, confidence: float) -> bool:
        """Return whether confidence is sufficient."""
        return confidence >= self.threshold(decision_type)
