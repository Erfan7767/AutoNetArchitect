"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class RedundancyDiagnostic(SpecializedDiagnostic):
    """Diagnose device_issue using explicit evidence and read-only checks."""

    diagnostic_id = "redundancy_diagnostic"
    symptom_class = "device_issue"
    required_evidence_types = ('redundancy', 'fhrp', 'log',)
    command_catalog = ('show redundancy', 'show standby', 'show vrrp', 'show logging',)
    findings_terms = (('failover', 'redundancy failover indicator is present'), ('standby', 'standby state requires validation'), ('split', 'split-brain or dual-active indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "redundancy_diagnostic", "nodes": [{"condition": "failover", "action": "redundancy failover indicator is present"}, {"condition": "standby", "action": "standby state requires validation"}, {"condition": "split", "action": "split-brain or dual-active indicator is present"}]})
