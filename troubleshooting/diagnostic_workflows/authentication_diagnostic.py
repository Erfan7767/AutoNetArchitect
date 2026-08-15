"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class AuthenticationDiagnostic(SpecializedDiagnostic):
    """Diagnose authentication_failure using explicit evidence and read-only checks."""

    diagnostic_id = "authentication_diagnostic"
    symptom_class = "authentication_failure"
    required_evidence_types = ('aaa', 'log', 'config',)
    command_catalog = ('show aaa servers', 'show authentication sessions', 'show logging', 'show access-lists',)
    findings_terms = (('fail', 'authentication failure indicator is present'), ('timeout', 'authentication service timeout is present'), ('certificate', 'certificate validation indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "authentication_diagnostic", "nodes": [{"condition": "fail", "action": "authentication failure indicator is present"}, {"condition": "timeout", "action": "authentication service timeout is present"}, {"condition": "certificate", "action": "certificate validation indicator is present"}]})
