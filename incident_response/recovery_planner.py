"""Service recovery planning for incident response."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import RecoveryPlan, RecoveryServiceStep


class RecoveryPlanner:
    """Build ordered recovery plans without executing service changes."""

    ORDER = {"core": 1, "distribution": 2, "access": 3, "non_critical": 4}

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def plan(self, *, incident_id: str, services: Sequence[Mapping[str, Any]], mode: str = "full_recovery", monitoring_confirmation_required: bool = True, user_confirmation_required: bool = False) -> RecoveryPlan:
        """Return a dependency-ordered recovery plan."""
        if mode not in {"full_recovery", "partial_recovery", "degraded_mode"}:
            raise ValueError("unsupported recovery mode")
        if not services:
            self.assumptions.append(make_assumption(f"{incident_id}:recovery_services", "not_supplied", "recovery order cannot be inferred without explicit services", True))
        steps: list[RecoveryServiceStep] = []
        for index, item in enumerate(services, start=1):
            service_id = str(item.get("service_id", ""))
            if not service_id:
                self.assumptions.append(make_assumption(f"{incident_id}:recovery_service:{index}", "missing_id", "service recovery item is skipped when no stable ID is supplied", True))
                continue
            tier = str(item.get("tier", "non_critical"))
            order = self.ORDER.get(tier, self.ORDER["non_critical"])
            if tier not in self.ORDER:
                self.assumptions.append(make_assumption(f"{incident_id}:recovery_tier:{service_id}", tier, "unknown tier is handled conservatively as non-critical", True))
            dependencies = [str(value) for value in item.get("dependencies", [])]
            steps.append(RecoveryServiceStep(service_id=service_id, recovery_action=str(item.get("recovery_action", "restore service through governed procedure")), verification_criteria=[str(value) for value in item.get("verification_criteria", ["monitoring confirms availability"])], estimated_time=timedelta(minutes=int(item["estimated_minutes"])) if item.get("estimated_minutes") is not None else None, dependencies=dependencies, priority_order=order, confirmation_source=str(item.get("confirmation_source", "monitoring_or_human_required"))))
        steps.sort(key=lambda step: (step.priority_order, step.service_id))
        criteria = ["connectivity tests pass", "service availability tests pass", "monitoring confirms stable state"]
        if user_confirmation_required:
            criteria.append("affected-user or service-owner confirmation is recorded")
        decision = make_decision("RecoveryPlanner", f"{incident_id}:recovery", mode, "recover in explicit dependency order and require verification before closure", ["full_recovery", "partial_recovery", "degraded_mode"], {item: "not selected by requested mode" for item in ["full_recovery", "partial_recovery", "degraded_mode"] if item != mode})
        self.decisions.append(decision)
        return RecoveryPlan(plan_id=f"{incident_id}:recovery-plan", mode=mode, services=steps, verification_criteria=criteria, monitoring_confirmation_required=monitoring_confirmation_required, user_confirmation_required=user_confirmation_required, execution_allowed=False, assumptions=[item.key for item in self.assumptions])
