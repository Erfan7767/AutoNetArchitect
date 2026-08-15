"""Scope boundaries for traffic analysis."""
from __future__ import annotations
from typing import Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_decision
from .models import ScopeEvaluation, ScopeStatus

class TrafficScopeBoundary:
    """Block out-of-scope packet and content inspection explicitly."""
    OUT_OF_SCOPE = {"dpi": "deep packet inspection is out of scope", "apm": "application performance monitoring is out of scope", "eue": "end-user experience monitoring is out of scope", "packet_capture": "Wireshark-level packet capture is out of scope", "content_inspection": "content inspection is out of scope", "malware_detection": "malware detection in traffic is out of scope"}
    IN_SCOPE = {"traffic_estimation", "bandwidth_calculation", "capacity_planning", "oversubscription", "bottleneck_detection", "baseline", "anomaly_detection", "flow_analysis", "qos_utilization", "wan_utilization"}
    def __init__(self) -> None:
        """Initialize scope state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def check(self, subject: str) -> ScopeEvaluation:
        """Evaluate one subject against the explicit scope matrix."""
        key = subject.strip().lower()
        if key in self.OUT_OF_SCOPE:
            status = ScopeStatus.OUT_OF_SCOPE
            reason = self.OUT_OF_SCOPE[key]
            action = "use a separately governed security/APM/packet-analysis capability"
            preview = False
        elif key in self.IN_SCOPE:
            status = ScopeStatus.IN_SCOPE
            reason = "subject is within Traffic and Capacity Analysis scope"
            action = None
            preview = False
        else:
            status = ScopeStatus.INSUFFICIENT_EVIDENCE
            reason = "subject is not defined in the V1 traffic scope matrix"
            action = "request human scope decision before analysis"
            preview = True
        decision = make_decision("TrafficScopeBoundary", f"scope:{key}", status.value, reason, [item.value for item in ScopeStatus], {item.value: "not selected by scope policy" for item in ScopeStatus if item != status})
        self.decisions.append(decision)
        return ScopeEvaluation(status=status, subject=subject, reason=reason, required_human_action=action, preview_only=preview, decision_id=decision.decision_id)
