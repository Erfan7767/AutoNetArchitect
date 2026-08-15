from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class MobilityWirelessProfile(HospitalDomainBase):
    """Mobility and wireless baseline for clinical movement and dense care areas."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "planning_modes": ["heuristic_baseline", "predictive_rf_when_site_inputs_exist", "survey_backed_for_production_claims"],
            "clinical_mobility_profiles": ["patient_monitoring", "clinical_staff_roaming", "asset_tracking", "voice_over_wifi", "infusion_or_biomedical_mobility"],
            "inputs_required": ["floor_dimensions", "materials", "mounting_height", "client_density", "interference_profile", "roaming_targets"],
            "controls": ["wpa3_or_supported_enterprise_authentication", "separate_ssids_and_policies", "fast_roaming_only_when_validated", "rf_survey_for_sensitive_areas"],
            "confidence_policy": "downgrade_or_pending_survey_when_inputs_are_missing",
        }
        review = self.clinical_review(requirements, "clinical_wireless_mobility")
        artifact["clinical_review"] = review
        self.record_decision("hospital_mobility_wireless", artifact["planning_modes"], "Wireless planning evidence level controls whether a production claim is permitted.")
        return self.envelope(requirements, artifact)
