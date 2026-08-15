"""False-negative and abstention correctness metrics."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner
from .design_quality_metrics import MetricResult


class AbstentionObservation(BaseModel):
    """One labeled abstention decision."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str
    system_abstained: bool
    abstention_was_expected: bool
    unsafe_action_taken: bool = False
    evidence_ids: tuple[str, ...] = ()


class FalseNegativeMetrics(BaseDesigner):
    """Calculate abstention correctness and false-negative safety metrics."""

    def __init__(self) -> None:
        """Initialize calculator."""
        super().__init__("FalseNegativeMetrics")
        self.record_decision("false_negative_policy", "abstention_labeled", "abstention correctness is measured against expected abstention labels")

    def calculate(self, observations: Iterable[AbstentionObservation]) -> tuple[MetricResult, ...]:
        """Calculate abstention correctness and unsafe-action miss rate."""
        items = tuple(observations)
        denominator = len(items)
        evidence = tuple(dict.fromkeys(evidence_id for item in items for evidence_id in item.evidence_ids))
        correct = sum(item.system_abstained == item.abstention_was_expected for item in items)
        unsafe_misses = sum(item.unsafe_action_taken for item in items)
        return (MetricResult(metric_name="abstention_correctness_rate", numerator=correct, denominator=denominator, rate=correct / denominator if denominator else None, interpretation="abstention decisions matching the expert-labeled expected behavior", evidence_ids=evidence), MetricResult(metric_name="unsafe_action_miss_rate", numerator=unsafe_misses, denominator=denominator, rate=unsafe_misses / denominator if denominator else None, interpretation="unsafe actions observed among labeled abstention cases", evidence_ids=evidence))
