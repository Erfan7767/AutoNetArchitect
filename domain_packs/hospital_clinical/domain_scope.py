from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class HospitalClinicalNetworksPack(HospitalDomainBase):
    """Entry point that keeps clinical scope explicit and non-clinical claims bounded."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        self.record_decision(
            "hospital_domain_activation",
            "hospital_clinical",
            "Activate technical network patterns for clinical and administrative environments without clinical approval claims.",
            alternatives=["enterprise_corporate_pack", "banking_pack"],
            rejection_reasons={"clinical_validity": "Network design does not establish clinical safety or medical device approval."},
        )
        return self.envelope(
            requirements,
            {
                "status": "active",
                "in_scope": [
                    "clinical_and_non_clinical_segmentation",
                    "medical_device_network_constraints",
                    "mobility_and_wireless_baseline",
                    "imaging_and_pacs_connectivity",
                    "guest_staff_patient_access",
                    "network_resilience",
                ],
                "out_of_scope": [
                    "clinical_safety_approval",
                    "medical_device_certification",
                    "clinical_workflow_design",
                    "medical_treatment_decisions",
                    "regulatory_certification",
                ],
                "clinical_review_policy": "mandatory_human_review_for_sensitive_paths",
            },
        )
