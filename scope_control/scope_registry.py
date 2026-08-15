"""Central scope registry and critical workflow boundary checks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
@dataclass(frozen=True)
class BoundaryCheck:
    """A boundary check with explicit outcome classification."""
    boundary_id: str
    category: str
    check: Callable[[dict[str, Any]], bool]
    status_if_failed: str
    reason: str
    workflow: str
    preview_available: bool = False
@dataclass
class ScopeResult:
    """Aggregated scope result for one workflow stage."""
    allowed: bool
    workflow: str
    violations: list[dict[str, Any]] = field(default_factory=list)
class ScopeRegistry:
    """Run registered boundaries before design, generation, deployment, or evaluation."""
    WORKFLOWS = {"design", "generation", "deployment", "evaluation"}
    def __init__(self, checks: list[BoundaryCheck] | None = None) -> None: self.checks = checks or self.default_checks()
    @staticmethod
    def default_checks() -> list[BoundaryCheck]:
        """Return conservative baseline checks."""
        return [BoundaryCheck("vendor_support", "vendor", lambda c: c.get("vendor") == "Huawei", "unsupported", "vendor is outside V1 support scope", "all", True), BoundaryCheck("scale_limit", "scale", lambda c: c.get("devices", 0) <= 500, "unsupported", "device count exceeds validated scale", "all", True), BoundaryCheck("regulatory_context", "regulatory", lambda c: c.get("regulatory_context") in {None, "general"}, "human_review", "regulated context requires human review", "deployment", False)]
    def check(self, workflow: str, context: dict[str, Any]) -> ScopeResult:
        """Run all applicable checks and return explicit violations."""
        if workflow not in self.WORKFLOWS: raise ValueError("unknown workflow")
        violations = []
        for boundary in self.checks:
            if boundary.workflow not in {"all", workflow}: continue
            if not boundary.check(context): violations.append({"boundary_id": boundary.boundary_id, "category": boundary.category, "status": boundary.status_if_failed, "reason": boundary.reason, "workflow": workflow, "preview_available": boundary.preview_available})
        return ScopeResult(not violations, workflow, violations)
