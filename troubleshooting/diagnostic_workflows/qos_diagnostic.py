"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class QoSDiagnostic(SpecializedDiagnostic):
    """Diagnose performance_degradation using explicit evidence and read-only checks."""

    diagnostic_id = "qos_diagnostic"
    symptom_class = "performance_degradation"
    required_evidence_types = ('qos', 'monitoring', 'interface',)
    command_catalog = ('show policy-map interface', 'show queueing interface', 'show interfaces',)
    findings_terms = (('drop', 'QoS queue drop indicator is present'), ('congest', 'congestion indicator is present'), ('class', 'QoS classification requires validation'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "qos_diagnostic", "nodes": [{"condition": "drop", "action": "QoS queue drop indicator is present"}, {"condition": "congest", "action": "congestion indicator is present"}, {"condition": "class", "action": "QoS classification requires validation"}]})
