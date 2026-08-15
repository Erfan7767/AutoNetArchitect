"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class RoutingDiagnostic(SpecializedDiagnostic):
    """Diagnose routing_issue using explicit evidence and read-only checks."""

    diagnostic_id = "routing_diagnostic"
    symptom_class = "routing_issue"
    required_evidence_types = ('route', 'neighbor', 'config',)
    command_catalog = ('show ip route', 'show ip protocols', 'show ip ospf neighbor', 'show ip bgp summary', 'show bfd neighbors',)
    findings_terms = (('idle', 'routing peer is idle'), ('active', 'routing peer is active but not established'), ('missing', 'expected route evidence is missing'), ('flap', 'route or adjacency flapping is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "routing_diagnostic", "nodes": [{"condition": "idle", "action": "routing peer is idle"}, {"condition": "active", "action": "routing peer is active but not established"}, {"condition": "missing", "action": "expected route evidence is missing"}, {"condition": "flap", "action": "route or adjacency flapping is present"}]})
