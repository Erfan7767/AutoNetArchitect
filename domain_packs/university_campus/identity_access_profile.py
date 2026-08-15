from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class IdentityAccessProfile(UniversityDomainBase):
    """Identity-aware access patterns for students, faculty, staff, guests, and researchers."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "identities": ["student", "faculty", "staff", "researcher", "contractor", "guest", "service_account", "device_identity"],
            "access_decisions": ["identity", "device_posture_when_required", "location_or_network_context", "resource_classification"],
            "controls": ["802.1x_where_supported", "mab_for_exception_devices", "mfa_for_admin_and_sensitive_resources", "least_privilege", "short_lived_guest_access", "sponsor_ownership"],
            "research_exception": "named_sponsor_and_expiry_required",
            "operations": ["joiner_mover_leaver_integration", "identity_event_logging", "access_review"],
        }
        self.record_decision("university_identity_access", artifact["identities"], "Identity and ownership determine access across academic, administrative, research, and residential contexts.")
        return self.envelope(requirements, artifact)
