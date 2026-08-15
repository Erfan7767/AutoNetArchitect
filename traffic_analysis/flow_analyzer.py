"""NetFlow/sFlow/IPFIX flow analysis."""
from __future__ import annotations
from collections import defaultdict
from typing import Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import FlowAnalysisReport, FlowRecord

class FlowAnalyzer:
    """Analyze explicit flow records and clearly mark absent flow data."""
    def __init__(self) -> None:
        """Initialize flow analysis state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def analyze(self, flows: Sequence[FlowRecord]) -> FlowAnalysisReport:
        """Return top talkers, applications, pairs, and source-destination matrix."""
        if not flows:
            self.assumptions.append(make_assumption("flow-analysis:data", "missing", "flow analysis requires NetFlow/sFlow/IPFIX records", True))
            return FlowAnalysisReport(available=False, patterns=["flow data not available"], assumptions=[item.key for item in self.assumptions])
        sources: dict[str, int] = defaultdict(int)
        destinations: dict[str, int] = defaultdict(int)
        pairs: dict[str, int] = defaultdict(int)
        apps: dict[str, int] = defaultdict(int)
        matrix: dict[str, int] = defaultdict(int)
        for flow in flows:
            sources[flow.source_ip] += flow.bytes_count
            destinations[flow.destination_ip] += flow.bytes_count
            pairs[f"{flow.source_ip}->{flow.destination_ip}"] += flow.bytes_count
            apps[flow.application or f"{flow.protocol}/{flow.destination_port or 'unknown'}"] += flow.bytes_count
            matrix[f"{flow.source_subnet or 'unknown'}->{flow.destination_subnet or 'unknown'}"] += flow.bytes_count
        patterns = ["client_server" if any(flow.source_subnet != flow.destination_subnet for flow in flows) else "peer_to_peer"]
        if any(flow.destination_ip == "255.255.255.255" for flow in flows):
            patterns.append("broadcast_or_multicast_candidate")
        report = FlowAnalysisReport(available=True, top_source_ips=[{"source_ip": key, "bytes": value} for key, value in sorted(sources.items(), key=lambda item: item[1], reverse=True)[:10]], top_destination_ips=[{"destination_ip": key, "bytes": value} for key, value in sorted(destinations.items(), key=lambda item: item[1], reverse=True)[:10]], top_pairs=[{"pair": key, "bytes": value} for key, value in sorted(pairs.items(), key=lambda item: item[1], reverse=True)[:10]], top_applications=[{"application": key, "bytes": value} for key, value in sorted(apps.items(), key=lambda item: item[1], reverse=True)[:10]], traffic_matrix=[{"matrix": key, "bytes": value} for key, value in sorted(matrix.items(), key=lambda item: item[1], reverse=True)], patterns=patterns, evidence_ids=list(dict.fromkeys(flow.evidence_id for flow in flows)))
        self.decisions.append(make_decision("FlowAnalyzer", "flow-analysis", "aggregate_explicit_flow_records", "aggregate only supplied records; no packet capture or DPI is performed", ["aggregate_explicit_flow_records", "inspect_packet_payloads"], {"aggregate_explicit_flow_records": "selected", "inspect_packet_payloads": "out of scope"}))
        return report
