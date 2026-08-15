"""Repeatable reliability statistics with conservative confidence intervals."""
from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class ReliabilityStatistic(BaseModel):
    """A bounded rate with an explicit confidence interval."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str
    successes: int
    trials: int
    rate: float | None
    confidence_level: float
    lower_bound: float | None
    upper_bound: float | None
    method: str = "wilson_score_interval"
    evidence_ids: tuple[str, ...] = ()


class ReliabilityStatistics(BaseDesigner):
    """Calculate deterministic binomial reliability statistics."""

    def __init__(self, confidence_level: float = 0.95) -> None:
        """Initialize statistics calculator."""
        super().__init__("ReliabilityStatistics")
        if not 0.0 < confidence_level < 1.0:
            raise ValueError("confidence level must be between zero and one")
        self.confidence_level = confidence_level
        self.record_decision("reliability_statistics_policy", "wilson_interval", "reported rates retain sample size and interval bounds")

    def calculate(self, metric_name: str, successes: int, trials: int, *, evidence_ids: tuple[str, ...] = ()) -> ReliabilityStatistic:
        """Calculate a Wilson interval without external statistical dependencies."""
        if trials < 0 or successes < 0 or successes > trials:
            raise ValueError("successes and trials must satisfy zero <= successes <= trials")
        if trials == 0:
            return ReliabilityStatistic(metric_name=metric_name, successes=successes, trials=trials, rate=None, confidence_level=self.confidence_level, lower_bound=None, upper_bound=None, evidence_ids=evidence_ids)
        z = self._z_value(self.confidence_level)
        p = successes / trials
        denominator = 1.0 + z * z / trials
        center = (p + z * z / (2.0 * trials)) / denominator
        margin = z * math.sqrt((p * (1.0 - p) / trials) + (z * z / (4.0 * trials * trials))) / denominator
        return ReliabilityStatistic(metric_name=metric_name, successes=successes, trials=trials, rate=p, confidence_level=self.confidence_level, lower_bound=max(0.0, center - margin), upper_bound=min(1.0, center + margin), evidence_ids=evidence_ids)

    @staticmethod
    def _z_value(confidence_level: float) -> float:
        """Return common two-sided normal critical values for supported levels."""
        table = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}
        closest = min(table, key=lambda key: abs(key - confidence_level))
        if abs(closest - confidence_level) > 0.01:
            raise ValueError("confidence_level must be approximately 0.90, 0.95, or 0.99")
        return table[closest]
