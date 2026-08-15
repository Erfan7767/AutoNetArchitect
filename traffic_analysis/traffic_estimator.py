"""Traffic estimation from explicit user and device profiles."""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import LinkType, TrafficComposition, TrafficData, TrafficLinkModel, TrafficSource

class TrafficEstimator:
    """Estimate traffic only from explicit profile counts and marked assumptions."""
    DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
        "office_worker": {"avg_mbps": 0.5, "peak_mbps": 2.0, "composition": {"data": 60, "voice": 15, "video": 20, "other": 5}},
        "developer": {"avg_mbps": 1.0, "peak_mbps": 5.0, "composition": {"data": 70, "voice": 10, "video": 15, "other": 5}},
        "executive": {"avg_mbps": 1.5, "peak_mbps": 8.0, "composition": {"data": 50, "voice": 10, "video": 35, "other": 5}},
        "student": {"avg_mbps": 0.8, "peak_mbps": 4.0, "composition": {"data": 55, "voice": 10, "video": 30, "other": 5}},
        "medical_staff": {"avg_mbps": 1.0, "peak_mbps": 10.0, "composition": {"data": 45, "voice": 10, "video": 35, "other": 10}},
        "iot_device": {"avg_mbps": 0.01, "peak_mbps": 0.1, "composition": {"data": 85, "voice": 0, "video": 0, "other": 15}},
        "camera": {"avg_mbps": 4.0, "peak_mbps": 8.0, "composition": {"data": 0, "voice": 0, "video": 95, "other": 5}},
    }
    def __init__(self, profiles: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        """Initialize profile catalog."""
        self.profiles = {key: dict(value) for key, value in (profiles or self.DEFAULT_PROFILES).items()}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def estimate_link(self, *, link_id: str, source_device: str, source_interface: str, destination_device: str, destination_interface: str, link_speed_mbps: float, link_type: LinkType, user_profile_counts: Mapping[str, int], devices_served: int | None = None, diversity_factor: float | None = None) -> TrafficLinkModel:
        """Estimate one link from profile counts and an explicit diversity factor."""
        if not user_profile_counts:
            raise ValueError("user_profile_counts is HumanSuppliedMandatory for estimation")
        for profile, count in user_profile_counts.items():
            if profile not in self.profiles:
                raise ValueError(f"unsupported traffic profile: {profile}")
            if int(count) < 0:
                raise ValueError("profile counts cannot be negative")
        factor = diversity_factor if diversity_factor is not None else {LinkType.ACCESS_UPLINK: 1.0, LinkType.DISTRIBUTION_UPLINK: 0.5, LinkType.CORE_LINK: 0.4, LinkType.WAN_LINK: 0.3, LinkType.SERVER_LINK: 0.5}.get(link_type, 0.4)
        if not 0 < factor <= 1:
            raise ValueError("diversity_factor must be between zero and one")
        total_users = sum(int(value) for value in user_profile_counts.values())
        avg_mbps = sum(int(count) * float(self.profiles[name]["avg_mbps"]) for name, count in user_profile_counts.items())
        peak_mbps = sum(int(count) * float(self.profiles[name]["peak_mbps"]) for name, count in user_profile_counts.items()) * factor
        weighted = {key: 0.0 for key in ("data", "voice", "video", "other")}
        for name, count in user_profile_counts.items():
            profile = self.profiles[name]
            for key in weighted:
                weighted[key] += int(count) * float(profile.get("composition", {}).get(key, 0))
        total_weight = sum(weighted.values()) or 1.0
        composition = TrafficComposition(data_percent=weighted["data"] * 100 / total_weight, voice_percent=weighted["voice"] * 100 / total_weight, video_percent=weighted["video"] * 100 / total_weight, management_percent=0.0, other_percent=weighted["other"] * 100 / total_weight)
        confidence = {LinkType.ACCESS_UPLINK: 0.65, LinkType.DISTRIBUTION_UPLINK: 0.5, LinkType.CORE_LINK: 0.4, LinkType.WAN_LINK: 0.3, LinkType.SERVER_LINK: 0.45}.get(link_type, 0.25)
        assumption = make_assumption(f"traffic-estimate:{link_id}:diversity", factor, "simultaneous peak usage is estimated with an explicit diversity factor", True)
        self.assumptions.append(assumption)
        data = TrafficData(source=TrafficSource.ESTIMATED, avg_utilization_percent=min(100.0, avg_mbps * 100 / link_speed_mbps), peak_utilization_percent=min(100.0, peak_mbps * 100 / link_speed_mbps), avg_bps_in=int(avg_mbps * 1_000_000), avg_bps_out=int(avg_mbps * 1_000_000), peak_bps_in=int(peak_mbps * 1_000_000), peak_bps_out=int(peak_mbps * 1_000_000), confidence=confidence, assumptions=[assumption.key])
        link = TrafficLinkModel(link_id=link_id, source_device=source_device, source_interface=source_interface, destination_device=destination_device, destination_interface=destination_interface, link_speed_mbps=link_speed_mbps, link_type=link_type, traffic_data=data, traffic_composition=composition, users_served=total_users, devices_served=devices_served, assumptions=[assumption.key])
        decision = make_decision("TrafficEstimator", f"traffic-estimate:{link_id}", "profile_count_times_bandwidth", "estimate from explicit profile counts and reduce aggregation confidence", ["profile_count_times_bandwidth", "invent_traffic_rate"], {"profile_count_times_bandwidth": "selected", "invent_traffic_rate": "rejected"})
        self.decisions.append(decision)
        return link
