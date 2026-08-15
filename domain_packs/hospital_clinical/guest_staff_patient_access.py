from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class GuestStaffPatientAccess(HospitalDomainBase):
    """Separate guest, staff, patient, and clinical access paths."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "access_domains": {
                "guest": "internet_only_with_client_isolation",
                "patient": "internet_or_explicit_patient_services_only",
                "staff": "identity_based_access_to_authorized_corporate_and_clinical_services",
                "clinical_staff": "clinical_services_with_stronger_device_and_identity_policy",
                "clinical_devices": "device_specific_allowlist_and_no_public_access",
            },
            "controls": ["mfa_for_staff_and_admin", "nac_or_equivalent_when_supported", "rate_limits_for_public_access", "dns_and_content_policy", "no_lateral_guest_to_clinical_access"],
            "review": self.clinical_review(requirements, "patient_and_clinical_access"),
        }
        self.record_decision("hospital_access_separation", artifact["access_domains"], "Public, staff, and clinical paths are separated with explicit service allowlists.")
        return self.envelope(requirements, artifact)
