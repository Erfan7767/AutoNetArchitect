"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class DHCPDiagnostic(SpecializedDiagnostic):
    """Diagnose dns_dhcp_issue using explicit evidence and read-only checks."""

    diagnostic_id = "dhcp_diagnostic"
    symptom_class = "dns_dhcp_issue"
    required_evidence_types = ('dhcp', 'relay', 'vlan',)
    command_catalog = ('show ip dhcp binding', 'show ip dhcp pool', 'show ip helper-address', 'show logging',)
    findings_terms = (('exhaust', 'DHCP scope exhaustion indicator is present'), ('relay', 'DHCP relay indicator is present'), ('no ip', 'client address allocation is missing'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "dhcp_diagnostic", "nodes": [{"condition": "exhaust", "action": "DHCP scope exhaustion indicator is present"}, {"condition": "relay", "action": "DHCP relay indicator is present"}, {"condition": "no ip", "action": "client address allocation is missing"}]})
