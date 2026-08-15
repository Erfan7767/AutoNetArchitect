"""Traffic performance baselines and comparison."""
from __future__ import annotations
from typing import Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision, statistics
from .models import BaselineStatistics

class BaselineManager:
    """Create and compare statistical baselines from explicit samples."""
    def __init__(self) -> None:
        """Initialize baseline store."""
        self.baselines: dict[tuple[str, str, str], BaselineStatistics] = {}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def create(self, *, subject_id: str, metric: str, period_label: str, values: Sequence[float], evidence_ids: Sequence[str] = ()) -> BaselineStatistics:
        """Create a baseline and retain sample provenance."""
        if not values:
            raise ValueError("baseline requires explicit values")
        stats = statistics(values)
        baseline = BaselineStatistics(subject_id=subject_id, metric=metric, period_label=period_label, sample_count=len(values), average=stats["average"], median=stats["median"], percentile_95=stats["percentile_95"], standard_deviation=stats["standard_deviation"], minimum=stats["minimum"], maximum=stats["maximum"], source_evidence_ids=list(evidence_ids))
        self.baselines[(subject_id, metric, period_label)] = baseline
        self.decisions.append(make_decision("BaselineManager", f"baseline:{subject_id}:{metric}:{period_label}", "create_statistical_baseline", "calculate baseline statistics from supplied samples", ["create_statistical_baseline", "guess_baseline"], {"create_statistical_baseline": "selected", "guess_baseline": "rejected"}))
        return baseline
    def compare(self, baseline: BaselineStatistics, *, current_value: float) -> dict[str, float | str | bool]:
        """Compare one current observation with a baseline."""
        if baseline.average is None:
            return {"status": "unknown", "deviation": 0.0, "anomalous": False}
        deviation = current_value - baseline.average
        threshold = (baseline.standard_deviation or 0.0) * 3
        anomalous = abs(deviation) > threshold if threshold > 0 else current_value != baseline.average
        status = "degraded" if anomalous else "within_baseline"
        return {"status": status, "deviation": deviation, "anomalous": anomalous}
