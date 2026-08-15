from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingPrivilegedAccessPatterns(BankingDomainBase):
    """Privileged network administration and break-glass control patterns."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        pattern = {
            "admin_network": "dedicated_management_plane",
            "access": ["mfa", "jump_host_or_pam", "device_identity", "role_based_authorization"],
            "separation": ["operator_vs_approver", "security_admin_vs_network_admin", "production_vs_lab"],
            "break_glass": ["time_bound", "dual_authorization", "session_recording", "post_event_review"],
            "protocols": ["ssh_or_vendor_secure_protocol", "snmpv3", "api_tls"],
            "direct_user_access_to_infrastructure": "prohibited_by_default",
        }
        self.record_decision("banking_privileged_access", pattern["admin_network"], "Privileged paths are isolated, authenticated, approved, and recorded.")
        return self.envelope(requirements, pattern)
