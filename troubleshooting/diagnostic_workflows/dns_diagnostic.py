"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class DNSDiagnostic(SpecializedDiagnostic):
    """Diagnose dns_dhcp_issue using explicit evidence and read-only checks."""

    diagnostic_id = "dns_diagnostic"
    symptom_class = "dns_dhcp_issue"
    required_evidence_types = ('dns', 'resolver', 'log',)
    command_catalog = ('show ip dns view', 'show hosts', 'show logging',)
    findings_terms = (('nxdomain', 'DNS negative response indicator is present'), ('timeout', 'DNS timeout indicator is present'), ('unreachable', 'DNS resolver is unreachable'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "dns_diagnostic", "nodes": [{"condition": "nxdomain", "action": "DNS negative response indicator is present"}, {"condition": "timeout", "action": "DNS timeout indicator is present"}, {"condition": "unreachable", "action": "DNS resolver is unreachable"}]})
