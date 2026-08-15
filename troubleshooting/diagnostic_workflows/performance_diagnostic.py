"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class PerformanceDiagnostic(SpecializedDiagnostic):
    """Diagnose performance_degradation using explicit evidence and read-only checks."""

    diagnostic_id = "performance_diagnostic"
    symptom_class = "performance_degradation"
    required_evidence_types = ('interface', 'monitoring', 'qos', 'log',)
    command_catalog = ('show interfaces', 'show processes cpu', 'show processes memory', 'show policy-map interface', 'show queueing interface',)
    findings_terms = (('drop', 'output or queue drops are present'), ('crc', 'physical errors may affect performance'), ('latency', 'latency indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "performance_diagnostic", "nodes": [{"condition": "drop", "action": "output or queue drops are present"}, {"condition": "crc", "action": "physical errors may affect performance"}, {"condition": "latency", "action": "latency indicator is present"}]})
