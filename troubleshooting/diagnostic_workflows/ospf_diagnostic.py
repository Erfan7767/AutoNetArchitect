"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class OSPFDiagnostic(SpecializedDiagnostic):
    """Diagnose routing_issue using explicit evidence and read-only checks."""

    diagnostic_id = "ospf_diagnostic"
    symptom_class = "routing_issue"
    required_evidence_types = ('ospf', 'route', 'interface',)
    command_catalog = ('show ip ospf neighbor', 'show ip ospf interface', 'show ip ospf database', 'show ip route ospf',)
    findings_terms = (('init', 'OSPF neighbor is in INIT'), ('exstart', 'OSPF database exchange may have MTU mismatch'), ('full', 'OSPF FULL state is present and requires route validation'), ('2way', 'OSPF 2WAY state requires network-type interpretation'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "ospf_diagnostic", "nodes": [{"condition": "init", "action": "OSPF neighbor is in INIT"}, {"condition": "exstart", "action": "OSPF database exchange may have MTU mismatch"}, {"condition": "full", "action": "OSPF FULL state is present and requires route validation"}, {"condition": "2way", "action": "OSPF 2WAY state requires network-type interpretation"}]})
