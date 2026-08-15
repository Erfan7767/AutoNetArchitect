"""Oversubscription analysis by network tier and domain."""
from __future__ import annotations
from typing import Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import CapacityStatus, OversubscriptionFinding

class OversubscriptionAnalyzer:
    """Compare explicit downstream capacity to explicit uplink capacity."""
    DEFAULT_GUIDELINES = {"enterprise_office": {"access_to_distribution": 20.0, "distribution_to_core": 4.0, "core_to_wan": 1.0, "server_to_core": 4.0}, "banking": {"access_to_distribution": 10.0, "distribution_to_core": 2.0, "core_to_wan": 1.0}, "hospital": {"access_to_distribution": 10.0, "distribution_to_core": 2.0, "core_to_wan": 1.0}, "university": {"access_to_distribution": 20.0, "distribution_to_core": 4.0, "core_to_wan": 1.0}, "data_center": {"server_to_leaf": 3.0, "leaf_to_spine": 3.0}}
    def __init__(self, guidelines: Mapping[str, Mapping[str, float]] | None = None) -> None:
        """Initialize guideline catalog."""
        self.guidelines = {key: dict(value) for key, value in (guidelines or self.DEFAULT_GUIDELINES).items()}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def analyze(self, *, subject_id: str, tier: str, downstream_capacities_mbps: Sequence[float], uplink_capacity_mbps: float, domain: str = "enterprise_office") -> OversubscriptionFinding:
        """Assess one oversubscription ratio."""
        if uplink_capacity_mbps <= 0 or not downstream_capacities_mbps:
            raise ValueError("explicit downstream and uplink capacities are mandatory")
        theoretical = sum(float(value) for value in downstream_capacities_mbps)
        ratio = theoretical / uplink_capacity_mbps
        guideline = self.guidelines.get(domain, {}).get(tier)
        if guideline is None:
            self.assumptions.append(make_assumption(f"oversubscription:{subject_id}:guideline", "unknown", "no domain guideline was supplied for the requested tier", True))
            status = CapacityStatus.UNKNOWN
            rationale = "ratio calculated but no authoritative domain guideline is available"
        else:
            status = CapacityStatus.UPGRADE_REQUIRED if ratio > guideline else CapacityStatus.WARNING if ratio >= guideline * 0.8 else CapacityStatus.HEALTHY
            rationale = f"ratio={ratio:.2f}:1 compared with guideline={guideline:.2f}:1"
        decision = make_decision("OversubscriptionAnalyzer", f"oversubscription:{subject_id}", status.value, "compare explicit capacities against a domain-specific guideline", ["healthy", "warning", "upgrade_required", "unknown"], {item: "not selected by ratio or evidence" for item in ["healthy", "warning", "upgrade_required", "unknown"] if item != status.value})
        self.decisions.append(decision)
        return OversubscriptionFinding(subject_id=subject_id, tier=tier, theoretical_max_input_mbps=theoretical, actual_uplink_capacity_mbps=uplink_capacity_mbps, ratio=ratio, guideline_ratio=guideline, status=status, rationale=rationale, assumptions=[item.key for item in self.assumptions])
