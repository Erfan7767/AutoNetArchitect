"""Brownfield complexity boundaries."""
class BrownfieldComplexityBoundaries:
    """Detect incomplete brownfield evidence and dependency complexity."""
    def check(self, context: dict[str, object]) -> dict[str, object]:
        """Return complexity status."""
        if context.get("environment") != "brownfield": return {"status": "not_applicable"}
        if context.get("unknown_dependencies", 0) > 0 or context.get("undiscovered_devices", 0) > 0: return {"status": "insufficient_evidence", "required_action": "complete inventory and dependency discovery"}
        return {"status": "within_scope"}
