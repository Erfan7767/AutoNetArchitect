"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class PhysicalLayerDiagnostic(SpecializedDiagnostic):
    """Diagnose device_issue using explicit evidence and read-only checks."""

    diagnostic_id = "physical_layer_diagnostic"
    symptom_class = "device_issue"
    required_evidence_types = ('interface', 'optic', 'environment',)
    command_catalog = ('show interfaces', 'show interfaces counters errors', 'show interfaces transceiver', 'show environment', 'show power inline',)
    findings_terms = (('crc', 'CRC errors indicate a physical or duplex issue'), ('errdisable', 'errdisable state is present'), ('temperature', 'thermal indicator is present'), ('power', 'power or PoE indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "physical_layer_diagnostic", "nodes": [{"condition": "crc", "action": "CRC errors indicate a physical or duplex issue"}, {"condition": "errdisable", "action": "errdisable state is present"}, {"condition": "temperature", "action": "thermal indicator is present"}, {"condition": "power", "action": "power or PoE indicator is present"}]})
