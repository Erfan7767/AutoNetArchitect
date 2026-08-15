"""Deployment success metrics."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner
from .design_quality_metrics import MetricResult


class DeploymentObservation(BaseModel):
    """One measured deployment outcome."""

    model_config = ConfigDict(extra="forbid")

    deployment_id: str
    attempted: bool = True
    success: bool
    unsafe_recommendation: bool = False
    evidence_ids: tuple[str, ...] = ()


class DeploymentSuccessMetrics(BaseDesigner):
    """Calculate deployment success and unsafe recommendation rates."""

    def __init__(self) -> None:
        """Initialize calculator."""
        super().__init__("DeploymentSuccessMetrics")
        self.record_decision("deployment_metric_policy", "observed_outcomes_only", "deployment metrics require recorded attempts and outcomes")

    def calculate(self, observations: Iterable[DeploymentObservation]) -> tuple[MetricResult, ...]:
        """Calculate success rate and unsafe recommendation rate."""
        items = tuple(item for item in observations if item.attempted)
        denominator = len(items)
        evidence = tuple(dict.fromkeys(evidence_id for item in items for evidence_id in item.evidence_ids))
        success = sum(item.success for item in items)
        unsafe = sum(item.unsafe_recommendation for item in items)
        return (MetricResult(metric_name="deployment_success_rate", numerator=success, denominator=denominator, rate=success / denominator if denominator else None, interpretation="observed deployment successes divided by recorded attempts", evidence_ids=evidence), MetricResult(metric_name="unsafe_recommendation_rate", numerator=unsafe, denominator=denominator, rate=unsafe / denominator if denominator else None, interpretation="observed unsafe recommendations divided by recorded deployment attempts", evidence_ids=evidence))
