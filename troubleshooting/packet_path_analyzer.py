"""Logical packet-path analysis without protocol emulation or live writes."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from .models import EvidenceCollection


class PathHop(BaseModel):
    """One logical hop in a packet path."""

    model_config = ConfigDict(extra="forbid")

    hop_number: int
    device_id: str
    interface_in: str = ""
    interface_out: str = ""
    decision: str = "forward"
    route: str = ""
    acl_action: str = "not_evaluated"
    nat_action: str = "not_evaluated"
    evidence_ids: list[str] = Field(default_factory=list)


class PacketPath(BaseModel):
    """Result of a bounded logical packet-path analysis."""

    model_config = ConfigDict(extra="forbid")

    source_ip: str
    destination_ip: str
    protocol: str
    port: int | None = None
    hops: list[PathHop] = Field(default_factory=list)
    drop_point: PathHop | None = None
    drop_reason: str = ""
    nat_translations: list[dict[str, Any]] = Field(default_factory=list)
    filtered_by: list[str] = Field(default_factory=list)
    unexpected_path: bool = False
    total_path_latency_estimate: float | None = None
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate port and confidence bounds."""
        if self.port is not None and not 0 <= self.port <= 65535:
            raise ValueError("packet port must be between zero and 65535")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("packet path confidence must be between zero and one")


class PacketPathAnalyzer:
    """Analyze expected path data without claiming full forwarding-plane emulation."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def analyze(self, source_ip: str, destination_ip: str, protocol: str, port: int | None = None, *, design_data: Mapping[str, Any] | None = None, evidence: EvidenceCollection | None = None) -> PacketPath:
        """Trace a logical path from explicit design and parsed evidence."""
        if not source_ip or not destination_ip:
            raise ValueError("source_ip and destination_ip are required")
        design = dict(design_data or {})
        evidence_items = list(evidence.items) if evidence else []
        evidence_ids = [item.evidence_id for item in evidence_items]
        hops: list[PathHop] = []
        raw_hops = design.get("path_hops", design.get("hops", []))
        if isinstance(raw_hops, Sequence) and not isinstance(raw_hops, (str, bytes)):
            for index, raw in enumerate(raw_hops, start=1):
                if isinstance(raw, Mapping):
                    hops.append(PathHop(hop_number=index, device_id=str(raw.get("device_id", raw.get("device", f"hop-{index}"))), interface_in=str(raw.get("interface_in", "")), interface_out=str(raw.get("interface_out", "")), decision=str(raw.get("decision", "forward")), route=str(raw.get("route", "")), acl_action=str(raw.get("acl_action", "not_evaluated")), nat_action=str(raw.get("nat_action", "not_evaluated")), evidence_ids=[str(item) for item in raw.get("evidence_ids", evidence_ids)]))
        if not hops:
            self.assumptions.append(Assumption("packet_path_hops", "not_supplied", "logical hops cannot be invented when topology or route data is absent", True))
        drop_point = next((hop for hop in hops if hop.decision.lower() in {"drop", "deny", "blocked", "discard"} or hop.acl_action.lower() in {"deny", "drop", "blocked"}), None)
        filtered = [hop.device_id for hop in hops if hop.acl_action.lower() in {"deny", "drop", "blocked"}]
        nat = [{"device_id": hop.device_id, "action": hop.nat_action} for hop in hops if hop.nat_action.lower() not in {"not_evaluated", "none", "no_nat"}]
        confidence = 0.8 if design.get("path_hops") else 0.35 if evidence_items else 0.1
        result = PacketPath(source_ip=source_ip, destination_ip=destination_ip, protocol=protocol, port=port, hops=hops, drop_point=drop_point, drop_reason="ACL/firewall or hop decision explicitly indicates drop" if drop_point else "", nat_translations=nat, filtered_by=filtered, unexpected_path=bool(design.get("unexpected_path", False)), total_path_latency_estimate=float(design["total_path_latency_estimate"]) if design.get("total_path_latency_estimate") is not None else None, confidence=confidence, assumptions=[item.key for item in self.assumptions], evidence_ids=evidence_ids)
        self.decisions.append(DecisionRecord("PacketPathAnalyzer", f"packet-path:{source_ip}->{destination_ip}", "bounded_logical_path", "use only explicit design and evidence hops", ["bounded_logical_path", "protocol_emulation"], {"bounded_logical_path": "selected in V1", "protocol_emulation": "out of scope without an emulator"}))
        return result
