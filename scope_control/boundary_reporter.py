"""Scope violation reporting."""
from __future__ import annotations
class BoundaryReporter:
    """Aggregate boundary outcomes across workflows."""
    def report(self, results: list[object]) -> dict[str, object]:
        """Return violations grouped by workflow and status."""
        violations = [violation for result in results for violation in getattr(result, "violations", [])]; by_status: dict[str, int] = {}
        for violation in violations: by_status[violation["status"]] = by_status.get(violation["status"], 0) + 1
        return {"violation_count": len(violations), "by_status": by_status, "violations": violations}
