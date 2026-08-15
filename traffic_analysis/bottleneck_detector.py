"""Traffic bottleneck detection."""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import BottleneckFinding, BottleneckType, FindingSeverity, TrafficLinkModel

class BottleneckDetector:
    """Detect sustained utilization and explicit error/latency bottlenecks."""
    def __init__(self, utilization_threshold: float = 70.0) -> None:
        """Initialize threshold policy."""
        if not 0 < utilization_threshold <= 100:
            raise ValueError("utilization threshold must be between zero and one hundred")
        self.utilization_threshold = utilization_threshold
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def detect(self, links: Sequence[TrafficLinkModel], *, observations: Mapping[str, Mapping[str, float]] | None = None) -> list[BottleneckFinding]:
        """Detect capacity, error, latency, packet-loss, or device-resource findings."""
        output: list[BottleneckFinding] = []
        obs = observations or {}
        for link in links:
            data = link.traffic_data
            peak = data.peak_utilization_percent
            if peak is not None and peak > self.utilization_threshold:
                output.append(BottleneckFinding(finding_id=f"bottleneck:{link.link_id}:utilization", location=f"{link.source_device}:{link.source_interface}->{link.destination_device}:{link.destination_interface}", bottleneck_type=BottleneckType.BANDWIDTH, severity=FindingSeverity.CRITICAL if peak >= 90 else FindingSeverity.WARNING, current_value=peak, threshold=self.utilization_threshold, impact_description="link utilization exceeds the sustained planning threshold", recommendation="increase capacity, rebalance traffic, or validate QoS after change governance", evidence_ids=data.evidence_ids, confidence=data.confidence, assumptions=data.assumptions))
            item = obs.get(link.link_id, {})
            for key, label, threshold, finding_type in (("errors", "interface errors", 0.0, BottleneckType.BANDWIDTH), ("latency_ms", "latency", 100.0, BottleneckType.BANDWIDTH), ("packet_loss_percent", "packet loss", 1.0, BottleneckType.BANDWIDTH), ("cpu_percent", "device CPU", 85.0, BottleneckType.CPU), ("memory_percent", "device memory", 85.0, BottleneckType.MEMORY), ("sessions_percent", "session table", 85.0, BottleneckType.SESSION)):
                value = item.get(key)
                if value is None or (key == "errors" and value <= threshold) or (key != "errors" and value <= threshold):
                    continue
                output.append(BottleneckFinding(finding_id=f"bottleneck:{link.link_id}:{key}", location=link.link_id, bottleneck_type=finding_type, severity=FindingSeverity.CRITICAL if value >= threshold * 1.2 else FindingSeverity.WARNING, current_value=value, threshold=threshold, impact_description=f"explicit {label} observation exceeds threshold", recommendation="validate the underlying capacity or device resource with operations evidence", evidence_ids=[str(value) for value in item.get("evidence_ids", [])], confidence=0.7, assumptions=[]))
        if not links:
            self.assumptions.append(make_assumption("bottleneck:links", "none", "no link data was supplied; no bottleneck conclusion is made", True))
        self.decisions.append(make_decision("BottleneckDetector", "bottleneck-detection", "evidence_thresholds_only", "emit findings only for explicit threshold observations", ["evidence_thresholds_only", "infer_bottleneck_from_topology_names"], {"evidence_thresholds_only": "selected", "infer_bottleneck_from_topology_names": "rejected"}))
        return output
