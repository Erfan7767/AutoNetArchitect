"""Bandwidth requirement calculations."""
from __future__ import annotations
from typing import Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import BandwidthRequirement, CapacityStatus, TrafficLinkModel

class BandwidthCalculator:
    """Calculate capacity requirements from measured or estimated traffic."""
    def __init__(self) -> None:
        """Initialize calculation state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def calculate_link(self, link: TrafficLinkModel, *, overhead_percent: float = 12.5, headroom_percent: float = 30.0) -> BandwidthRequirement:
        """Calculate one link requirement with explicit overhead and headroom policy."""
        if not 0 <= overhead_percent <= 100 or not 0 <= headroom_percent <= 100:
            raise ValueError("overhead and headroom must be percentages")
        data = link.traffic_data
        peak_bps = max(value or 0 for value in (data.peak_bps_in, data.peak_bps_out))
        required = peak_bps / 1_000_000 * (1 + overhead_percent / 100) * (1 + headroom_percent / 100)
        current_util = max(value or 0 for value in (data.peak_utilization_percent, data.avg_utilization_percent)) if any(value is not None for value in (data.peak_utilization_percent, data.avg_utilization_percent)) else None
        upgrade = required > link.link_speed_mbps
        status = CapacityStatus.UPGRADE_REQUIRED if upgrade else CapacityStatus.WARNING if current_util is not None and current_util >= 70 else CapacityStatus.HEALTHY if current_util is not None else CapacityStatus.UNKNOWN
        if data.source.value == "estimated":
            self.assumptions.append(make_assumption(f"bandwidth:{link.link_id}:traffic_source", "estimated", "required bandwidth uses estimated traffic and is not a collected capacity proof", True))
        decision = make_decision("BandwidthCalculator", f"bandwidth:{link.link_id}", status.value, "apply explicit protocol overhead and headroom to the supplied peak rate", ["apply_policy_overhead", "omit_headroom"], {"apply_policy_overhead": "selected", "omit_headroom": "rejected"})
        self.decisions.append(decision)
        return BandwidthRequirement(subject_id=link.link_id, current_capacity_mbps=link.link_speed_mbps, required_bandwidth_mbps=required, current_utilization_percent=current_util, headroom_percent=max(0.0, (link.link_speed_mbps - required) * 100 / link.link_speed_mbps), overhead_percent=overhead_percent, upgrade_needed=upgrade, status=status, contributors={"peak_traffic": peak_bps / 1_000_000}, evidence_ids=list(dict.fromkeys([*data.evidence_ids, *link.evidence_ids])), assumptions=[item.key for item in self.assumptions])

    def calculate_wan(self, subject_id: str, *, components_mbps: Mapping[str, float], current_capacity_mbps: float | None, overhead_percent: float = 12.5, headroom_percent: float = 30.0) -> BandwidthRequirement:
        """Calculate WAN capacity from explicitly supplied components."""
        if not components_mbps:
            raise ValueError("WAN components are HumanSuppliedMandatory")
        if any(float(value) < 0 for value in components_mbps.values()):
            raise ValueError("WAN components cannot be negative")
        base = sum(float(value) for value in components_mbps.values())
        required = base * (1 + overhead_percent / 100) * (1 + headroom_percent / 100)
        status = CapacityStatus.UNKNOWN if current_capacity_mbps is None else CapacityStatus.UPGRADE_REQUIRED if required > current_capacity_mbps else CapacityStatus.HEALTHY
        if current_capacity_mbps is None:
            self.assumptions.append(make_assumption(f"bandwidth:{subject_id}:capacity", "unknown", "current WAN capacity was not supplied", True))
        return BandwidthRequirement(subject_id=subject_id, current_capacity_mbps=current_capacity_mbps, required_bandwidth_mbps=required, headroom_percent=((current_capacity_mbps - required) * 100 / current_capacity_mbps) if current_capacity_mbps else None, overhead_percent=overhead_percent, upgrade_needed=None if current_capacity_mbps is None else required > current_capacity_mbps, status=status, contributors={key: float(value) for key, value in components_mbps.items()}, assumptions=[item.key for item in self.assumptions])
