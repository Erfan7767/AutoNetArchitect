from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner


class UniversityDomainBase(BaseDesigner):
    """Auditable, opt-in base contract for University and Campus patterns."""

    domain_id = "university_campus"
    supported_sector_values = {"university", "higher_education", "education", "university_campus"}
    integration_targets = {
        "requirements": "requirements.requirements_analyzer.RequirementsAnalyzer",
        "wireless": "wireless_rf.wireless_confidence_evaluator",
        "security": "designers.security.security_designer",
        "services": "designers.dns_dhcp.dns_dhcp_designer",
        "operations": "operations",
        "formal_verification": "formal_verification.verification_reporter.VerificationReporter",
        "field_reality": "field_reality.field_feasibility_checker",
        "equipment": "equipment_selector",
        "compliance": "compliance",
        "knowledge": "knowledge.claim_resolver.ClaimResolver",
    }

    def guard_domain(self, requirements: dict[str, Any]) -> dict[str, Any]:
        sector = requirements.get("sector", requirements.get("organization_type"))
        if sector is None:
            self.record_assumption("sector", self.domain_id, "University pack activation requires explicit university or higher-education selection.")
            return {"status": "sector_required", "domain_id": self.domain_id, "applicable": False, "reason": "Explicit university_campus selection is required."}
        applicable = str(sector).lower() in self.supported_sector_values
        if not applicable:
            self.record_decision("university_scope_guard", "rejected", "University patterns must not be generalized to another sector.", alternatives=["select_the_matching_sector_pack"], rejection_reasons={"requested_sector": f"{sector} is outside university_campus scope"})
            return {"status": "out_of_scope", "domain_id": self.domain_id, "applicable": False, "reason": f"Sector {sector!r} is outside this domain pack."}
        return {"status": "applicable", "domain_id": self.domain_id, "applicable": True, "sector": sector}

    def envelope(self, requirements: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_scope": "university_and_campus_network_architecture_only",
            "scope_guard": self.guard_domain(requirements),
            "artifact": artifact,
            "integration_targets": dict(self.integration_targets),
            "decisions": list(self.decisions),
            "assumptions": list(self.assumptions),
            "source_of_truth": requirements.get("source_of_truth", "requirements_document"),
            "academic_or_research_claim": "not_certified_by_network_domain_pack",
        }

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.envelope(requirements, {})
