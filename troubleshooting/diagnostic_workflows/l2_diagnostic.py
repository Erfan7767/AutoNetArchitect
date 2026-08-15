"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class L2Diagnostic(SpecializedDiagnostic):
    """Diagnose l2_issue using explicit evidence and read-only checks."""

    diagnostic_id = "l2_diagnostic"
    symptom_class = "l2_issue"
    required_evidence_types = ('vlan', 'trunk', 'mac',)
    command_catalog = ('show vlan', 'show interfaces trunk', 'show mac address-table', 'show interfaces switchport',)
    findings_terms = (('flap', 'MAC flapping indicator is present'), ('pruned', 'VLAN pruning indicator is present'), ('mismatch', 'Layer-2 mismatch indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "l2_diagnostic", "nodes": [{"condition": "flap", "action": "MAC flapping indicator is present"}, {"condition": "pruned", "action": "VLAN pruning indicator is present"}, {"condition": "mismatch", "action": "Layer-2 mismatch indicator is present"}]})
