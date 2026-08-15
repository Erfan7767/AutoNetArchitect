from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class UniversityEquipmentPreferences(UniversityDomainBase):
    """Vendor-neutral equipment preferences for diverse campus roles."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "selection_principles": ["role_and_scale_fit", "campus_lifecycle_support", "wireless_density_telemetry", "identity_access_support", "multicast_support_when_required", "research_throughput_and_protocol_evidence", "automation_and_operations_integration"],
            "role_preferences": {
                "campus_access": ["poe", "802.1x", "high_client_scale", "telemetry"],
                "campus_core": ["redundant_control", "high_speed_uplinks", "multicast_and_routing_scale"],
                "residential_access": ["high_client_density", "isolation", "central_management"],
                "research_edge": ["throughput", "jumbo_frame_evidence_when_needed", "special_protocol_validation"],
                "wireless": ["high_density", "roaming", "spectrum_telemetry", "identity_integration"],
            },
            "selection_guard": "No model is recommended without capability, lifecycle, lab, and operations evidence.",
        }
        self.record_decision("university_equipment_preferences", artifact["selection_principles"], "Equipment preferences preserve differences among campus roles and require evidence before selection.")
        return self.envelope(requirements, artifact)
