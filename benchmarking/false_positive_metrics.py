"""False-positive and unsafe recommendation metrics."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner
from .design_quality_metrics import MetricResult


class FalsePositiveObservation(BaseModel):
    """One case where the system made a positive claim or recommendation."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str
    recommendation_made: bool
    recommendation_was_unsafe: bool
    unsupported_claim_made: bool
    reference_expected_safe: bool
    evidence_ids: tuple[str, ...] = ()


class FalsePositiveMetrics(BaseDesigner):
    """Calculate measured unsafe and unsupported positive rates."""

    def __init__(self) -> None:
        """Initialize calculator."""
        super().__init__("FalsePositiveMetrics")
        self.record_decision("false_positive_policy", "reference_labeled", "false positive metrics require an expected reference label and are not inferred from absence of failure")

    def calculate(self, observations: Iterable[FalsePositiveObservation]) -> tuple[MetricResult, ...]:
        """Calculate unsafe recommendation and unsupported-claim rates."""
        items = tuple(item for item in observations if item.recommendation_made and item.reference_expected_safe)
        denominator = len(items)
        evidence = tuple(dict.fromkeys(evidence_id for item in items for evidence_id in item.evidence_ids))
        unsafe = sum(item.recommendation_was_unsafe for item in items)
        unsupported = sum(item.unsupported_claim_made for item in items)
        return (MetricResult(metric_name="unsafe_recommendation_rate", numerator=unsafe, denominator=denominator, rate=unsafe / denominator if denominator else None, interpretation="unsafe positive recommendations divided by labeled positive recommendations", evidence_ids=evidence), MetricResult(metric_name="unsupported_claim_rate", numerator=unsupported, denominator=denominator, rate=unsupported / denominator if denominator else None, interpretation="unsupported claims divided by labeled positive recommendations", evidence_ids=evidence))
