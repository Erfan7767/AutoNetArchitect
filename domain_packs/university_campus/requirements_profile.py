from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class UniversityRequirementsProfile(UniversityDomainBase):
    """Requirement profile for heterogeneous university populations and facilities."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "mandatory_inputs": ["campus_inventory", "academic_and_admin_populations", "research_facility_inventory", "residential_population", "wireless_density_by_area", "identity_sources", "shared_services", "multicast_video_use_cases"],
            "functional_profiles": {
                "academic": ["teaching_rooms", "learning_platforms", "faculty_access", "student_access"],
                "administrative": ["business_systems", "records", "finance", "hr"],
                "research": ["high_throughput", "special_protocols", "large_data_flows", "external_collaboration"],
                "residential": ["high_user_count", "personal_devices", "tenant_isolation", "variable_peak_demand"],
            },
            "default_objectives": ["identity_aware_access", "high_density_wireless", "research_exception_governance", "service_resilience", "operational_observability"],
            "unknown_input_policy": "require_human_input_or_mark_unresolved",
        }
        self.record_decision("university_requirements_profile", profile["functional_profiles"], "University requirements must preserve different usage, ownership, and performance models.")
        return self.envelope(requirements, profile)
