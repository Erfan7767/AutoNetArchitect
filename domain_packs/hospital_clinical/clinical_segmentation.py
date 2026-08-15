from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class ClinicalSegmentation(HospitalDomainBase):
    """Segmentation baseline separating clinical, administrative, and public access."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "clinical_critical_zones": ["patient_monitoring", "medical_devices", "pacs_imaging", "clinical_servers", "clinical_voice"],
            "non_clinical_zones": ["administrative", "staff_general", "guest", "patient_internet", "facilities_iot", "management"],
            "default_policy": "deny_between_zones_until_explicitly_approved",
            "special_boundaries": ["medical_devices_no_direct_guest_access", "patient_network_no_management_access", "clinical_paths_require_human_review"],
            "evidence_required": ["flow_matrix", "device_communication_matrix", "formal_verification", "change_approval"],
        }
        review = self.clinical_review(requirements, "clinical_segmentation")
        self.record_decision("hospital_clinical_segmentation", artifact["default_policy"], "Clinical and non-clinical zones require explicit, reviewed flows.")
        artifact["clinical_review"] = review
        return self.envelope(requirements, artifact)
