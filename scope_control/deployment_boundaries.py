"""Deployment-specific boundary checks."""
class DeploymentBoundaries:
    """Block production deployment for unknown or regulated contexts."""
    def check(self, context: dict[str, object]) -> dict[str, object]:
        """Return production status and required action."""
        if context.get("regulatory_context") not in (None, "general"): return {"status": "production-blocked", "required_action": "human compliance approval"}
        if not context.get("rollback_validated", False): return {"status": "production-blocked", "required_action": "validate rollback in lab"}
        return {"status": "allowed"}
