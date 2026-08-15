"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class IntermittentDiagnostic(SpecializedDiagnostic):
    """Diagnose connectivity_loss using explicit evidence and read-only checks."""

    diagnostic_id = "intermittent_diagnostic"
    symptom_class = "connectivity_loss"
    required_evidence_types = ('log', 'monitoring', 'interface',)
    command_catalog = ('show logging', 'show interfaces', 'show interfaces counters errors', 'show processes cpu history',)
    findings_terms = (('flap', 'a state flap indicator is present'), ('updown', 'a recurring interface state transition is present'), ('timeout', 'a timeout indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "intermittent_diagnostic", "nodes": [{"condition": "flap", "action": "a state flap indicator is present"}, {"condition": "updown", "action": "a recurring interface state transition is present"}, {"condition": "timeout", "action": "a timeout indicator is present"}]})
