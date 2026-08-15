from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseSecurityBaselines(EnterpriseDomainBase):
    """Baseline segmentation and security controls for enterprise networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        baselines = {
            "segments": ["staff", "guest", "voice", "iot", "management", "servers", "quarantine"],
            "default_boundary": "deny_between_segments_unless_explicitly_allowed",
            "identity_controls": ["802.1x_where_supported", "mab_exception_for_non_8021x_devices", "admin_mfa"],
            "edge_controls": ["stateful_firewall", "egress_filtering", "vpn_termination", "secure_management"],
            "logging": ["authentication", "administrative_changes", "security_policy", "wan_events"],
        }
        self.record_decision("enterprise_security_baseline", baselines["default_boundary"], "Enterprise segmentation defaults to explicit allow between trust zones.")
        return self.envelope(requirements, baselines)
