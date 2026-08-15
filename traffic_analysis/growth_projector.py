"""Traffic growth projection with explicit assumptions."""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision, statistics
from .models import GrowthModel, GrowthProjection

class GrowthProjector:
    """Project traffic with linear, exponential, step, or seasonal models."""
    DEFAULT_RATE = 25.0
    def __init__(self) -> None:
        """Initialize projection state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def project(self, *, subject_id: str, current_mbps: float, model: GrowthModel, annual_growth_rate_percent: float | None = None, historical_values_mbps: Sequence[float] = (), planned_additions: Mapping[str, float] | None = None, threshold_percent: float = 70.0) -> GrowthProjection:
        """Return 6-month, one-, two-, and three-year projections."""
        if current_mbps < 0:
            raise ValueError("current_mbps cannot be negative")
        rate = annual_growth_rate_percent
        if rate is None:
            rate = self.DEFAULT_RATE
            self.assumptions.append(make_assumption(f"growth:{subject_id}:rate", rate, "no historical or approved growth rate was supplied; V1 default is an assumption", True))
        if rate < -100:
            raise ValueError("annual growth rate cannot be below negative one hundred percent")
        years = (0.5, 1.0, 2.0, 3.0)
        additions = dict(planned_additions or {})
        projections: dict[str, float] = {}
        for period in years:
            if model == GrowthModel.LINEAR:
                value = current_mbps * (1 + rate / 100 * period)
            elif model == GrowthModel.EXPONENTIAL:
                value = current_mbps * ((1 + rate / 100) ** period)
            elif model == GrowthModel.STEP:
                numeric_additions = []
                for key, addition in additions.items():
                    try:
                        if float(key) <= period:
                            numeric_additions.append(float(addition))
                    except (TypeError, ValueError):
                        self.assumptions.append(make_assumption(f"growth:{subject_id}:step:{key}", addition, "step additions require numeric period keys; nonnumeric planned-event keys are not applied", True))
                value = current_mbps + sum(numeric_additions)
            else:
                value = current_mbps * (1 + rate / 100 * period) * (1 + 0.1 if int(period) % 2 == 1 else 1 - 0.05)
            projections[f"{int(period * 12)}_months"] = round(max(0.0, value), 6)
        confidence = 0.75 if historical_values_mbps else 0.35
        if historical_values_mbps:
            trend = statistics([float(value) for value in historical_values_mbps])
            self.assumptions.append(make_assumption(f"growth:{subject_id}:historical", trend, "historical values are used as evidence but do not prove future traffic", True))
        breach = None
        if current_mbps > 0:
            threshold_value = current_mbps * threshold_percent / 100
            for period, value in projections.items():
                if value >= threshold_value:
                    breach = period
                    break
        decision = make_decision("GrowthProjector", f"growth:{subject_id}", model.value, "apply the requested growth model and mark non-historical rate assumptions", [item.value for item in GrowthModel], {item.value: "not selected by requested model" for item in GrowthModel if item != model})
        self.decisions.append(decision)
        return GrowthProjection(subject_id=subject_id, model=model, base_value_mbps=current_mbps, projections_mbps=projections, growth_rate_percent_per_year=rate, threshold_percent=threshold_percent, threshold_breach_period=breach, historical_evidence_ids=[], assumptions=[item.key for item in self.assumptions], confidence=confidence)
