"""Specialized read-only diagnostic workflow."""

from __future__ import annotations

from .specialized_diagnostic import SpecializedDiagnostic


class VPNDiagnostic(SpecializedDiagnostic):
    """Diagnose vpn_issue using explicit evidence and read-only checks."""

    diagnostic_id = "vpn_diagnostic"
    symptom_class = "vpn_issue"
    required_evidence_types = ('vpn', 'route', 'nat',)
    command_catalog = ('show crypto ikev2 sa', 'show crypto ipsec sa', 'show vpn tunnel', 'show ip route',)
    findings_terms = (('phase', 'IKE phase indicator is present'), ('down', 'VPN tunnel is down'), ('selector', 'proxy identity or selector mismatch indicator is present'),)
    decision_tree = SpecializedDiagnostic.decision_tree.model_copy(update={"tree_id": "vpn_diagnostic", "nodes": [{"condition": "phase", "action": "IKE phase indicator is present"}, {"condition": "down", "action": "VPN tunnel is down"}, {"condition": "selector", "action": "proxy identity or selector mismatch indicator is present"}]})
