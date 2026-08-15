"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class ConnectivityDiagnostic(SpecializedDiagnostic):
    """Diagnose connectivity_loss using explicit evidence and read-only checks."""

    diagnostic_id = "connectivity_diagnostic"
    symptom_class = "connectivity_loss"
    required_evidence_types = ('interface', 'vlan', 'route', 'gateway', 'acl', 'nat',)
    command_catalog = ('show interfaces', 'show ip interface brief', 'show ip route', 'show arp', 'show access-lists',)
    findings_terms = (('down', 'interface or protocol state indicates down'), ('unreachable', 'a reachability failure is present'), ('deny', 'a policy deny indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "connectivity_diagnostic", "nodes": [{"condition": "down", "action": "interface or protocol state indicates down"}, {"condition": "unreachable", "action": "a reachability failure is present"}, {"condition": "deny", "action": "a policy deny indicator is present"}]})
