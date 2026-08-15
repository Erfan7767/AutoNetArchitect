"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class ACLFirewallDiagnostic(SpecializedDiagnostic):
    """Diagnose connectivity_loss using explicit evidence and read-only checks."""

    diagnostic_id = "acl_firewall_diagnostic"
    symptom_class = "connectivity_loss"
    required_evidence_types = ('acl', 'firewall', 'log',)
    command_catalog = ('show access-lists', 'show ip interface', 'show firewall policy', 'show logging',)
    findings_terms = (('deny', 'an explicit deny indicator is present'), ('implicit', 'implicit deny may be affecting traffic'), ('shadow', 'policy shadowing indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "acl_firewall_diagnostic", "nodes": [{"condition": "deny", "action": "an explicit deny indicator is present"}, {"condition": "implicit", "action": "implicit deny may be affecting traffic"}, {"condition": "shadow", "action": "policy shadowing indicator is present"}]})
