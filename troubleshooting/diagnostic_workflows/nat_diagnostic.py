"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class NATDiagnostic(SpecializedDiagnostic):
    """Diagnose vpn_issue using explicit evidence and read-only checks."""

    diagnostic_id = "nat_diagnostic"
    symptom_class = "vpn_issue"
    required_evidence_types = ('nat', 'route', 'acl',)
    command_catalog = ('show ip nat translations', 'show ip nat statistics', 'show access-lists', 'show ip route',)
    findings_terms = (('exhaust', 'NAT pool or port exhaustion indicator is present'), ('deny', 'NAT policy or ACL deny indicator is present'), ('missing', 'expected translation is missing'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "nat_diagnostic", "nodes": [{"condition": "exhaust", "action": "NAT pool or port exhaustion indicator is present"}, {"condition": "deny", "action": "NAT policy or ACL deny indicator is present"}, {"condition": "missing", "action": "expected translation is missing"}]})
