"""Rollback success metrics."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner
from .design_quality_metrics import MetricResult


class RollbackObservation(BaseModel):
    """One measured rollback outcome."""

    model_config = ConfigDict(extra="forbid")

    rollback_id: str
    required: bool
    success: bool
    scope_preserved: bool
    evidence_ids: tuple[str, ...] = ()


class RollbackSuccessMetrics(BaseDesigner):
    """Calculate rollback success and scope preservation."""

    def __init__(self) -> None:
        """Initialize calculator."""
        super().__init__("RollbackSuccessMetrics")
        self.record_decision("rollback_metric_policy", "measured_rollback_only", "rollback rate is calculated only from rollback attempts explicitly recorded")

    def calculate(self, observations: Iterable[RollbackObservation]) -> tuple[MetricResult, ...]:
        """Calculate rollback success and scope preservation rates."""
        items = tuple(item for item in observations if item.required)
        denominator = len(items)
        evidence = tuple(dict.fromkeys(evidence_id for item in items for evidence_id in item.evidence_ids))
        success = sum(item.success for item in items)
        preserved = sum(item.scope_preserved for item in items)
        return (MetricResult(metric_name="rollback_success_rate", numerator=success, denominator=denominator, rate=success / denominator if denominator else None, interpretation="observed successful rollbacks divided by required rollback attempts", evidence_ids=evidence), MetricResult(metric_name="rollback_scope_preservation_rate", numerator=preserved, denominator=denominator, rate=preserved / denominator if denominator else None, interpretation="observed rollback attempts that preserved declared scope", evidence_ids=evidence))
