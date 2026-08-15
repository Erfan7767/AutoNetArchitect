from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseRequirementsProfile(EnterpriseDomainBase):
    """Enterprise-specific requirement defaults without inventing site facts."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "mandatory_inputs": [
                "organization_size",
                "site_inventory",
                "hq_and_branch_count",
                "critical_services",
                "remote_user_population",
                "internet_and_wan_requirements",
                "regulatory_context_if_any",
            ],
            "recommended_capture": [
                "growth_horizon",
                "availability_targets",
                "voice_and_video_demand",
                "iot_population",
                "guest_access_model",
            ],
            "default_objectives": [
                "segmented_access",
                "resilient_hq_and_campus_core",
                "predictable_branch_connectivity",
                "secure_remote_access",
                "operational_observability",
            ],
            "human_supplied_fields": [
                "organization_size",
                "site_inventory",
                "exact_user_counts",
                "existing_equipment",
                "regulatory_context_if_any",
            ],
        }
        self.record_decision(
            "enterprise_requirements_profile",
            profile["default_objectives"],
            "Enterprise defaults establish priorities while preserving human-supplied site and population facts.",
        )
        return self.envelope(requirements, profile)
