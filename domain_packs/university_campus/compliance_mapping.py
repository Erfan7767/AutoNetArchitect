from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class UniversityComplianceMapping(UniversityDomainBase):
    """Maps supplied university obligations to network technical controls."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        obligations = requirements.get("compliance_obligations", [])
        mapping = {
            "identity_and_access": ["student_faculty_staff_identity", "admin_mfa", "sponsor_owned_guest_access"],
            "privacy_and_data": ["segmentation", "least_privilege", "logging", "research_exception_governance"],
            "availability": ["campus_core_redundancy", "wireless_capacity", "service_monitoring", "recovery_testing"],
            "operations": ["change_control", "configuration_backup", "incident_traceability", "ownership"],
            "research_governance": ["named_owner", "expiry", "flow_review", "bandwidth_accountability"],
        }
        status = "requires_authoritative_obligations" if not obligations else "mapped_pending_evidence"
        if not obligations:
            self.record_assumption("compliance_obligations", [], "Exact education, privacy, research, and jurisdictional obligations must be supplied authoritatively.")
        self.record_decision("university_compliance_mapping", mapping, "University obligations map to technical controls without asserting regulatory certification.")
        return self.envelope(requirements, {"status": status, "obligations": obligations, "control_mapping": mapping, "certification": "not_provided"})
