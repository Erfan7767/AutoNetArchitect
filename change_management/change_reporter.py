"""Reporting helpers for change management review and audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .change_metrics import ChangeMetrics, ChangeMetricsReport
from .change_models import ChangeRequest, ChangeStatus, ChangeType


@dataclass(frozen=True)
class ChangeReport:
    """Individual change report."""

    change: dict[str, Any]
    execution_timeline: tuple[dict[str, Any], ...]
    verification: dict[str, Any]
    documentation_complete: bool
    production_gate: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize individual report."""
        return asdict(self) | {"execution_timeline": list(self.execution_timeline)}


class ChangeReporter:
    """Generate local reports without assuming the reports layer or ITSM."""

    def individual(self, request: ChangeRequest) -> ChangeReport:
        """Generate a complete report for one request."""
        complete = bool(request.title and request.description and request.risk_assessment.rationale and request.implementation_plan.steps and request.rollback_plan.steps and request.verification_results.results)
        gate = "allow" if request.status == ChangeStatus.COMPLETED.value and request.verification_results.overall_status == "passed" else "block_or_review"
        return ChangeReport(request.to_dict(), tuple(event.to_dict() for event in request.execution_log), request.verification_results.to_dict(), complete, gate)

    def summary(self, requests: Iterable[ChangeRequest]) -> dict[str, Any]:
        """Generate weekly or monthly summary data from supplied requests."""
        values = tuple(requests)
        metrics = ChangeMetrics().calculate(values)
        return {"generated_at": datetime.now(timezone.utc).isoformat(), "metrics": metrics.to_dict(), "executed": [request.change_id for request in values if request.status in {ChangeStatus.COMPLETED.value, ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value}], "emergency": [request.change_id for request in values if request.change_type == ChangeType.EMERGENCY.value], "upcoming": [request.change_id for request in values if request.scheduled_window and request.scheduled_window.start_time > datetime.now(timezone.utc)]}

    def dashboard(self, requests: Iterable[ChangeRequest]) -> dict[str, Any]:
        """Generate management dashboard data."""
        values = tuple(requests)
        metrics = ChangeMetrics().calculate(values)
        risk_distribution: dict[str, int] = {}
        for request in values:
            risk = request.risk_assessment.risk_level
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        return {"change_velocity": metrics.total_changes, "success_rate": metrics.success_rate, "risk_distribution": dict(sorted(risk_distribution.items())), "rollback_rate": metrics.rollback_rate, "emergency_rate": metrics.emergency_rate}

    def compliance_audit(self, requests: Iterable[ChangeRequest]) -> dict[str, Any]:
        """Generate documentation completeness data for audit review."""
        values = tuple(requests)
        return {"total": len(values), "complete_documentation": [request.change_id for request in values if request.title and request.description and request.risk_assessment.rationale and request.implementation_plan.steps and request.rollback_plan.steps], "missing_rollback_plan": [request.change_id for request in values if not request.rollback_plan.steps], "missing_verification": [request.change_id for request in values if not request.verification_results.results], "emergency_without_review": [request.change_id for request in values if request.change_type == ChangeType.EMERGENCY.value and not request.lessons_learned]}
