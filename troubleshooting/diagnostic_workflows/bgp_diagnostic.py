"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class BGPDiagnostic(SpecializedDiagnostic):
    """Diagnose routing_issue using explicit evidence and read-only checks."""

    diagnostic_id = "bgp_diagnostic"
    symptom_class = "routing_issue"
    required_evidence_types = ('bgp', 'route', 'log',)
    command_catalog = ('show ip bgp summary', 'show ip bgp neighbors', 'show ip route', 'show logging',)
    findings_terms = (('idle', 'BGP peer is idle'), ('active', 'BGP peer is active but not established'), ('prefix', 'BGP prefix or maximum-prefix indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "bgp_diagnostic", "nodes": [{"condition": "idle", "action": "BGP peer is idle"}, {"condition": "active", "action": "BGP peer is active but not established"}, {"condition": "prefix", "action": "BGP prefix or maximum-prefix indicator is present"}]})
