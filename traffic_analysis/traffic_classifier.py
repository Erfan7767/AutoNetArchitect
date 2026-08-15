"""Traffic application, priority, and direction classification."""
from __future__ import annotations
from typing import Mapping
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import ClassificationMethod, FlowRecord, TrafficClassification, TrafficDirection, TrafficPriorityClass

class TrafficClassifier:
    """Classify flows with bounded port/DSCP/flow evidence."""
    PORTS = {80: ("web", TrafficPriorityClass.DEFAULT), 443: ("web", TrafficPriorityClass.DEFAULT), 25: ("email", TrafficPriorityClass.DEFAULT), 143: ("email", TrafficPriorityClass.DEFAULT), 993: ("email", TrafficPriorityClass.DEFAULT), 445: ("file_transfer", TrafficPriorityClass.SCAVENGER), 2049: ("file_transfer", TrafficPriorityClass.SCAVENGER), 21: ("file_transfer", TrafficPriorityClass.SCAVENGER), 5060: ("voice", TrafficPriorityClass.REAL_TIME), 5061: ("voice", TrafficPriorityClass.REAL_TIME), 3306: ("database", TrafficPriorityClass.BUSINESS_CRITICAL), 5432: ("database", TrafficPriorityClass.BUSINESS_CRITICAL), 22: ("management", TrafficPriorityClass.BUSINESS_CRITICAL), 161: ("management", TrafficPriorityClass.BUSINESS_CRITICAL), 162: ("management", TrafficPriorityClass.BUSINESS_CRITICAL), 123: ("management", TrafficPriorityClass.BUSINESS_CRITICAL)}
    def __init__(self, port_map: Mapping[int, tuple[str, TrafficPriorityClass]] | None = None) -> None:
        """Initialize port mapping."""
        self.port_map = dict(port_map or self.PORTS)
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def classify(self, flow: FlowRecord, *, source_zone: str | None = None, destination_zone: str | None = None, dscp: int | None = None) -> TrafficClassification:
        """Classify one flow without DPI or content inspection."""
        application = flow.application or "unknown"
        priority = TrafficPriorityClass.DEFAULT
        method = ClassificationMethod.FLOW_BASED if flow.application else ClassificationMethod.UNKNOWN
        confidence = 0.35 if flow.application else 0.15
        if flow.destination_port in self.port_map:
            application, priority = self.port_map[flow.destination_port]
            method = ClassificationMethod.DSCP_BASED if dscp is not None else ClassificationMethod.PORT_BASED
            confidence = 0.7 if dscp is None else 0.8
        elif dscp in {46, 34}:
            application = "real_time"
            priority = TrafficPriorityClass.REAL_TIME
            method = ClassificationMethod.DSCP_BASED
            confidence = 0.75
        if method == ClassificationMethod.UNKNOWN:
            self.assumptions.append(make_assumption(f"classification:{flow.protocol}:{flow.destination_port}", "unknown", "no supported port, DSCP, or application evidence was supplied", True))
        if source_zone == "server" and destination_zone == "server":
            direction = TrafficDirection.EAST_WEST
        elif source_zone == "management" or destination_zone == "management":
            direction = TrafficDirection.MANAGEMENT
        elif source_zone is not None or destination_zone is not None:
            direction = TrafficDirection.NORTH_SOUTH
        else:
            direction = TrafficDirection.UNKNOWN
        if direction == TrafficDirection.UNKNOWN:
            self.assumptions.append(make_assumption(f"classification:direction:{flow.source_ip}:{flow.destination_ip}", "unknown", "zones were not supplied; direction is not inferred from IP address text", True))
        decision = make_decision("TrafficClassifier", f"classification:{flow.source_ip}:{flow.destination_ip}:{flow.destination_port}", {"application": application, "priority": priority.value}, "use explicit flow application, supported ports, and optional DSCP evidence without DPI", ["port_or_flow_classification", "deep_packet_inspection"], {"port_or_flow_classification": "selected", "deep_packet_inspection": "out of scope"})
        self.decisions.append(decision)
        return TrafficClassification(application=application, priority_class=priority, direction=direction, method=method, protocol=flow.protocol, port=flow.destination_port, confidence=confidence, evidence_ids=[flow.evidence_id], assumptions=[item.key for item in self.assumptions])
