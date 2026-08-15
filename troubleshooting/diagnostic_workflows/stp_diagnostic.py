"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class STPDiagnostic(SpecializedDiagnostic):
    """Diagnose l2_issue using explicit evidence and read-only checks."""

    diagnostic_id = "stp_diagnostic"
    symptom_class = "l2_issue"
    required_evidence_types = ('stp', 'log', 'interface',)
    command_catalog = ('show spanning-tree', 'show spanning-tree detail', 'show logging',)
    findings_terms = (('blocking', 'STP blocking state is present'), ('root', 'root bridge or root change indicator is present'), ('errdisable', 'errdisable or guard event is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "stp_diagnostic", "nodes": [{"condition": "blocking", "action": "STP blocking state is present"}, {"condition": "root", "action": "root bridge or root change indicator is present"}, {"condition": "errdisable", "action": "errdisable or guard event is present"}]})
