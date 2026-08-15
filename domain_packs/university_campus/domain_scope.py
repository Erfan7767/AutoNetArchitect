from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class UniversityCampusPack(UniversityDomainBase):
    """Entry point that preserves university function diversity."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        self.record_decision("university_domain_activation", "university_campus", "Activate distinct academic, administrative, research, residential, and public-access patterns.", alternatives=["enterprise_corporate_pack", "hospital_clinical_pack"], rejection_reasons={"single_template": "University functions have different trust, performance, and ownership models."})
        return self.envelope(requirements, {
            "status": "active",
            "functional_domains": ["academic", "administrative", "research", "residential", "student_services", "guest_public"],
            "in_scope": ["campus_core", "research_networks", "dormitory_access", "dense_wireless", "identity_access", "multicast_video", "shared_services"],
            "out_of_scope": ["academic_program_design", "research_methodology", "student_policy", "application_architecture", "regulatory_certification"],
            "diversity_policy": "do_not_collapse_functional_domains_into_one_default",
        })
