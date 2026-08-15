"""Design quality metrics against engineer baselines."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class DesignQualityObservation(BaseModel):
    """One measured comparison between system output and engineer reference."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    design_accepted: bool
    design_choice_match: bool
    assumption_quality_score: float
    unresolved_handling_correct: bool
    config_correctness_score: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def model_post_init(self, __context: object) -> None:
        """Validate quality scores."""
        if not 0.0 <= self.assumption_quality_score <= 1.0:
            raise ValueError("assumption_quality_score must be between zero and one")
        if self.config_correctness_score is not None and not 0.0 <= self.config_correctness_score <= 1.0:
            raise ValueError("config_correctness_score must be between zero and one")


class MetricResult(BaseModel):
    """Bounded metric result with numerator, denominator, and evidence."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str
    numerator: float
    denominator: int
    rate: float | None = None
    mean: float | None = None
    interpretation: str
    evidence_ids: tuple[str, ...] = ()


class DesignQualityMetrics(BaseDesigner):
    """Calculate design metrics without issuing maturity claims."""

    def __init__(self) -> None:
        """Initialize metric calculator."""
        super().__init__("DesignQualityMetrics")
        self.record_decision("metric_policy", "measured_only", "design quality outputs remain metric results and do not become engineer-equivalence claims")

    def calculate(self, observations: Iterable[DesignQualityObservation]) -> tuple[MetricResult, ...]:
        """Calculate acceptance, choice, assumption, unresolved, and config metrics."""
        items = tuple(observations)
        denominator = len(items)
        evidence = tuple(dict.fromkeys(evidence_id for item in items for evidence_id in item.evidence_ids))
        if denominator == 0:
            return (MetricResult(metric_name="design_acceptance_rate", numerator=0, denominator=0, rate=None, interpretation="not measured: no observations", evidence_ids=evidence),)
        results = [MetricResult(metric_name="design_acceptance_rate", numerator=sum(item.design_accepted for item in items), denominator=denominator, rate=sum(item.design_accepted for item in items) / denominator, interpretation="measured acceptance ratio against recorded review outcomes", evidence_ids=evidence), MetricResult(metric_name="design_choice_match_rate", numerator=sum(item.design_choice_match for item in items), denominator=denominator, rate=sum(item.design_choice_match for item in items) / denominator, interpretation="measured choice agreement with the engineer baseline", evidence_ids=evidence), MetricResult(metric_name="unresolved_handling_correctness_rate", numerator=sum(item.unresolved_handling_correct for item in items), denominator=denominator, rate=sum(item.unresolved_handling_correct for item in items) / denominator, interpretation="measured correctness of unresolved-input handling", evidence_ids=evidence)]
        results.append(MetricResult(metric_name="assumption_quality_mean", numerator=sum(item.assumption_quality_score for item in items), denominator=denominator, mean=sum(item.assumption_quality_score for item in items) / denominator, interpretation="mean scored assumption quality from reviewed comparisons", evidence_ids=evidence))
        config_items = tuple(item.config_correctness_score for item in items if item.config_correctness_score is not None)
        results.append(MetricResult(metric_name="config_correctness_mean", numerator=sum(config_items), denominator=len(config_items), mean=sum(config_items) / len(config_items) if config_items else None, interpretation="mean config correctness where it was actually measured", evidence_ids=evidence))
        self.record_decision("design_quality_metrics", [item.metric_name for item in results], "metrics were calculated only from supplied observations")
        return tuple(results)
