from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseRemoteWorkProfile(EnterpriseDomainBase):
    """Remote work baseline for managed and unmanaged enterprise users."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "access_modes": ["managed_device_vpn", "identity_aware_access", "browser_based_access_when_supported"],
            "identity": ["mfa", "conditional_access", "least_privilege"],
            "device": ["posture_check_when_required", "managed_certificate_or_device_identity"],
            "segmentation": "remote_users_receive only authorized application paths",
            "capacity": ["concurrent_session_model", "peak_bandwidth_model", "vpn_headend_capacity"],
            "logging": ["authentication", "session_start_stop", "policy_decisions"],
        }
        self.record_decision("enterprise_remote_work", profile["access_modes"], "Remote work uses identity, device, capacity, and audit controls.")
        return self.envelope(requirements, profile)
