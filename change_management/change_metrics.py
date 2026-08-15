"""Metrics for change-management performance and documentation quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .change_models import ChangeRequest, ChangeStatus, ChangeType, VerificationStatus


@dataclass(frozen=True)
class ChangeMetricsReport:
    """Aggregated change metrics."""

    total_changes: int
    by_type: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]
    completed: int
    failed: int
    rolled_back: int
    success_rate: float
    rollback_rate: float
    emergency_rate: float
    standard_rate: float
    outside_window_count: int
    complete_documentation_count: int
    rollback_plan_count: int
    post_implementation_review_count: int
    unauthorized_count: int
    average_request_to_update_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics report."""
        return asdict(self)


class ChangeMetrics:
    """Calculate deterministic metrics from local change records."""

    def calculate(self, requests: Iterable[ChangeRequest]) -> ChangeMetricsReport:
        """Calculate volume, success, timeliness, quality, and compliance metrics."""
        values = tuple(requests)
        total = len(values)
        by_type = self._count(values, "change_type")
        by_category = self._count(values, "change_category")
        by_priority = self._count(values, "priority")
        completed = sum(request.status == ChangeStatus.COMPLETED.value for request in values)
        failed = sum(request.status == ChangeStatus.FAILED.value for request in values)
        rolled_back = sum(request.status == ChangeStatus.ROLLED_BACK.value or request.closure_code in {"failed_rolled_back", "failed_partial"} for request in values)
        attempted = completed + failed + rolled_back
        documented = sum(bool(request.title and request.description and request.implementation_plan.steps and request.risk_assessment.rationale and request.rollback_plan.steps) for request in values)
        rollback_plans = sum(bool(request.rollback_plan.steps) for request in values)
        post_review = sum(request.change_type == ChangeType.EMERGENCY.value and bool(request.lessons_learned) for request in values)
        outside_window = sum(request.scheduled_window is None and request.status in {ChangeStatus.COMPLETED.value, ChangeStatus.FAILED.value, ChangeStatus.ROLLED_BACK.value} for request in values)
        unauthorized = sum(any(approval.decision == "rejected" for approval in request.approvals) and request.status in {ChangeStatus.COMPLETED.value, ChangeStatus.IN_PROGRESS.value} for request in values)
        average_update = sum(max(0.0, (request.updated_at - request.created_at).total_seconds()) for request in values) / total if total else 0.0
        return ChangeMetricsReport(total, by_type, by_category, by_priority, completed, failed, rolled_back, round(completed / attempted, 4) if attempted else 0.0, round(rolled_back / attempted, 4) if attempted else 0.0, round(by_type.get(ChangeType.EMERGENCY.value, 0) / total, 4) if total else 0.0, round(by_type.get(ChangeType.STANDARD.value, 0) / total, 4) if total else 0.0, outside_window, documented, rollback_plans, post_review, unauthorized, average_update)

    @staticmethod
    def _count(requests: Iterable[ChangeRequest], field_name: str) -> dict[str, int]:
        """Count a categorical request field."""
        result: dict[str, int] = {}
        for request in requests:
            key = str(getattr(request, field_name))
            result[key] = result.get(key, 0) + 1
        return dict(sorted(result.items()))
