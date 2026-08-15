"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class WirelessDiagnostic(SpecializedDiagnostic):
    """Diagnose wireless_issue using explicit evidence and read-only checks."""

    diagnostic_id = "wireless_diagnostic"
    symptom_class = "wireless_issue"
    required_evidence_types = ('wireless', 'aaa', 'monitoring',)
    command_catalog = ('show wireless client summary', 'show wireless ap summary', 'show logging', 'show authentication sessions',)
    findings_terms = (('associate', 'association failure indicator is present'), ('interference', 'interference indicator is present'), ('roam', 'roaming indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "wireless_diagnostic", "nodes": [{"condition": "associate", "action": "association failure indicator is present"}, {"condition": "interference", "action": "interference indicator is present"}, {"condition": "roam", "action": "roaming indicator is present"}]})
