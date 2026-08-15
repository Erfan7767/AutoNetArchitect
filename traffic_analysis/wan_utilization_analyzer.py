"""WAN utilization analysis."""
from __future__ import annotations
from typing import Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_decision, make_assumption
from .models import CapacityStatus, LinkType, TrafficLinkModel, WANUtilizationFinding

class WANUtilizationAnalyzer:
    """Analyze WAN link utilization and explicit cost information."""
    def __init__(self) -> None:
        """Initialize analyzer state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def analyze(self, links: Sequence[TrafficLinkModel], *, costs_per_mbps: Mapping[str, float] | None = None, cir_by_link: Mapping[str, float] | None = None, burst_by_link: Mapping[str, float] | None = None, vpn_by_link: Mapping[str, float] | None = None) -> list[WANUtilizationFinding]:
        """Return findings for explicitly identified WAN links."""
        costs = dict(costs_per_mbps or {})
        cir = dict(cir_by_link or {})
        burst = dict(burst_by_link or {})
        vpn = dict(vpn_by_link or {})
        findings: list[WANUtilizationFinding] = []
        for link in links:
            if link.link_type != LinkType.WAN_LINK:
                continue
            data = link.traffic_data
            peak = data.peak_utilization_percent
            status = CapacityStatus.UNKNOWN if peak is None else CapacityStatus.UPGRADE_REQUIRED if peak >= 90 else CapacityStatus.WARNING if peak >= 70 else CapacityStatus.HEALTHY
            findings.append(WANUtilizationFinding(link_id=link.link_id, utilization_percent=data.avg_utilization_percent, peak_utilization_percent=peak, data_percent=link.traffic_composition.data_percent, voice_percent=link.traffic_composition.voice_percent, video_percent=link.traffic_composition.video_percent, cir_utilization_percent=cir.get(link.link_id), burst_utilization_percent=burst.get(link.link_id), vpn_utilization_percent=vpn.get(link.link_id), cost_per_mbps=costs.get(link.link_id), status=status, evidence_ids=data.evidence_ids, assumptions=[] if link.link_id in costs else [f"wan:{link.link_id}:cost_unknown"] if costs else [f"wan:{link.link_id}:cost_data_missing"]))
        if not links:
            self.assumptions.append(make_assumption("wan:links", "none", "no WAN links were supplied", True))
        self.decisions.append(make_decision("WANUtilizationAnalyzer", "wan-utilization", "analyze_explicit_wan_links", "filter by explicit WAN link type and preserve missing cost data", ["analyze_explicit_wan_links", "infer_wan_from_names"], {"analyze_explicit_wan_links": "selected", "infer_wan_from_names": "rejected"}))
        return findings
