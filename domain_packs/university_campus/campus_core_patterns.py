from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class CampusCorePatterns(UniversityDomainBase):
    """Campus core patterns for academic, administrative, and residential buildings."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "architecture": "redundant_access_distribution_core_with_building_failure_domains",
            "access_roles": ["student_access", "faculty_access", "staff_access", "voice", "iot", "guest"],
            "distribution_roles": ["building_aggregation", "policy_boundary", "multicast_boundary"],
            "core_roles": ["campus_transit", "shared_services_transit", "research_transit"],
            "routing": "summarized_building_and_functional_prefixes",
            "failure_domains": ["access_stack", "building_distribution", "core_device", "power", "fiber_path"],
            "operations": ["central_telemetry", "configuration_backup", "maintenance_window"],
        }
        self.record_decision("university_campus_core", artifact["architecture"], "Campus core patterns separate building and functional failure domains.")
        return self.envelope(requirements, artifact)
