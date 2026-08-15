from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class HospitalRequirementsProfile(HospitalDomainBase):
    """Requirement profile that distinguishes clinical-critical and non-clinical domains."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "mandatory_inputs": [
                "facility_inventory",
                "clinical_service_inventory",
                "medical_device_inventory",
                "clinical_criticality_by_path",
                "pacs_and_imaging_flows",
                "wireless_mobility_population",
                "guest_staff_patient_access_model",
                "availability_and_recovery_targets",
            ],
            "clinical_critical_domains": ["life_safety_related", "patient_monitoring", "clinical_devices", "pacs_imaging", "medication_or_procedure_support"],
            "non_clinical_domains": ["administration", "guest_internet", "facilities_iot", "education", "finance", "general_corporate_services"],
            "mandatory_human_review": ["clinical_device_path", "patient_monitoring_path", "pacs_path", "emergency_communications_path"],
            "unknown_input_policy": "block_or_human_review_not_silent_defaulting",
        }
        self.record_decision("hospital_requirements_profile", profile["clinical_critical_domains"], "Clinical criticality determines stronger evidence, review, and availability expectations.")
        return self.envelope(requirements, profile)
