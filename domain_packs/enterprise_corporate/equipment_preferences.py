from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseEquipmentPreferences(EnterpriseDomainBase):
    """Non-binding equipment preference metadata consumed by equipment selection."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        preferences = {
            "selection_principles": [
                "support_lifecycle_and_security_updates",
                "documented_platform_evidence",
                "feature_parity_across_hq_and_branches",
                "redundant_power_and_uplinks_for_critical_roles",
                "automated_telemetry_and_api_support",
            ],
            "role_preferences": {
                "campus_access": ["poe", "802.1x", "stack_or_virtual_chassis_capability"],
                "distribution_core": ["redundant_supervisors_or_pairing", "high_speed_uplinks", "routing_scale"],
                "branch_edge": ["dual_wan", "vpn_or_sdwan_support", "central_management"],
                "security_edge": ["stateful_inspection", "vpn", "logging", "high_availability"],
                "wireless": ["controller_or_cloud_management", "wpa3_enterprise", "telemetry"],
            },
            "selection_guard": "No model is selected without inventory, capability evidence, and lifecycle data.",
        }
        self.record_decision("enterprise_equipment_preferences", preferences["selection_principles"], "Preferences constrain equipment selection without naming unsupported models.")
        return self.envelope(requirements, preferences)
