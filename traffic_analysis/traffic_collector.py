"""Passive traffic collection contracts and counter calculations."""
from __future__ import annotations
from datetime import timedelta
from typing import Any, Callable, Mapping, Sequence
from pydantic import BaseModel, ConfigDict, Field
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import FlowRecord, TrafficSample

class CollectionRequest(BaseModel):
    """Read-only collection request."""
    model_config = ConfigDict(extra="forbid")
    target_ids: list[str] = Field(default_factory=list)
    method: str
    poll_interval_seconds: int = Field(default=300, gt=0)
    retention_days: int = Field(default=30, gt=0)
    read_only: bool = True

class TrafficCollection(BaseModel):
    """Collected traffic artifact."""
    model_config = ConfigDict(extra="forbid")
    samples: list[TrafficSample] = Field(default_factory=list)
    flows: list[FlowRecord] = Field(default_factory=list)
    collection_method: str
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

class TrafficCollector:
    """Collect supplied read-only observations; never open a device session itself."""
    def __init__(self) -> None:
        """Initialize the collector."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def collect_snmp(self, request: CollectionRequest, samples: Sequence[TrafficSample]) -> TrafficCollection:
        """Validate explicit SNMP counter samples and return them unchanged."""
        if request.method != "snmp_counters" or not request.read_only:
            raise ValueError("SNMP collection requires method=snmp_counters and read_only=True")
        if request.poll_interval_seconds != 300:
            self.assumptions.append(make_assumption("collector:poll_interval", request.poll_interval_seconds, "the supplied polling interval differs from the V1 reference interval", True))
        evidence = list(dict.fromkeys(sample.evidence_id for sample in samples))
        decision = make_decision("TrafficCollector", "collection:snmp", "accept_read_only_samples", "passive samples are accepted only when the request is read-only", ["accept_read_only_samples", "execute_device_commands"], {"accept_read_only_samples": "selected", "execute_device_commands": "rejected"})
        self.decisions.append(decision)
        return TrafficCollection(samples=list(samples), collection_method=request.method, evidence_ids=evidence, limitations=[] if samples else ["no SNMP samples supplied"])

    def collect_flows(self, request: CollectionRequest, flows: Sequence[FlowRecord]) -> TrafficCollection:
        """Validate supplied NetFlow/sFlow/IPFIX records."""
        if request.method not in {"netflow", "sflow", "ipfix", "streaming_telemetry"} or not request.read_only:
            raise ValueError("flow collection requires a supported passive method and read_only=True")
        evidence = list(dict.fromkeys(flow.evidence_id for flow in flows))
        self.decisions.append(make_decision("TrafficCollector", f"collection:{request.method}", "accept_read_only_flows", "flow records are consumed as supplied and not collected through write operations", ["accept_read_only_flows", "active_probe"], {"accept_read_only_flows": "selected", "active_probe": "rejected"}))
        return TrafficCollection(flows=list(flows), collection_method=request.method, evidence_ids=evidence, limitations=[] if flows else ["no flow records supplied"])

    def collect_live_read_only(self, request: CollectionRequest, reader: Callable[[CollectionRequest], TrafficCollection]) -> TrafficCollection:
        """Call an injected read-only reader without implementing connectivity."""
        if not request.read_only:
            raise ValueError("live collection is blocked unless read_only=True")
        result = reader(request)
        if not isinstance(result, TrafficCollection):
            raise TypeError("live reader must return TrafficCollection")
        self.assumptions.append(make_assumption("collector:live_reader", "injected", "live connectivity and device impact are governed by the injected adapter", True))
        return result

    @staticmethod
    def counter_rate(previous: TrafficSample, current: TrafficSample, interval: timedelta) -> dict[str, float]:
        """Calculate octet rates from monotonic counters."""
        seconds = interval.total_seconds()
        if seconds <= 0:
            raise ValueError("interval must be positive")
        deltas = {"in_bps": current.in_octets - previous.in_octets, "out_bps": current.out_octets - previous.out_octets}
        if any(value < 0 for value in deltas.values()):
            raise ValueError("counter reset or wrap requires an explicit reset policy")
        return {key: value * 8 / seconds for key, value in deltas.items()}
