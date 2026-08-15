"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class FHRPDiagnostic(SpecializedDiagnostic):
    """Diagnose routing_issue using explicit evidence and read-only checks."""

    diagnostic_id = "fhrp_diagnostic"
    symptom_class = "routing_issue"
    required_evidence_types = ('fhrp', 'arp', 'log',)
    command_catalog = ('show standby', 'show vrrp', 'show glbp', 'show arp', 'show logging',)
    findings_terms = (('active', 'FHRP active/standby state requires validation'), ('down', 'FHRP state is down'), ('duplicate', 'duplicate gateway indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "fhrp_diagnostic", "nodes": [{"condition": "active", "action": "FHRP active/standby state requires validation"}, {"condition": "down", "action": "FHRP state is down"}, {"condition": "duplicate", "action": "duplicate gateway indicator is present"}]})
