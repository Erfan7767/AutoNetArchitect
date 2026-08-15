from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner


class BankingDomainBase(BaseDesigner):
    """Auditable, opt-in base contract for Banking Networks domain logic."""

    domain_id = "banking"
    supported_sector_values = {"banking", "bank"}
    integration_targets = {
        "requirements": "requirements.requirements_analyzer.RequirementsAnalyzer",
        "governance": "governance",
        "security": "designers.security.security_designer",
        "deployment": "deployment",
        "compliance": "compliance",
        "formal_verification": "formal_verification.verification_reporter.VerificationReporter",
        "knowledge": "knowledge.claim_resolver.ClaimResolver",
    }

    def guard_domain(self, requirements: dict[str, Any]) -> dict[str, Any]:
        sector = requirements.get("sector", requirements.get("organization_type"))
        if sector is None:
            self.record_assumption(
                "sector",
                self.domain_id,
                "Banking pack activation requires an explicit banking sector selection and is never implicit.",
            )
            return {
                "status": "sector_required",
                "domain_id": self.domain_id,
                "applicable": False,
                "reason": "Explicit banking sector selection is required.",
            }
        applicable = str(sector).lower() in self.supported_sector_values
        if not applicable:
            self.record_decision(
                "banking_scope_guard",
                "rejected",
                "Banking controls must not be generalized to a non-banking sector.",
                alternatives=["select_the_matching_sector_pack"],
                rejection_reasons={"requested_sector": f"{sector} is outside banking scope"},
            )
            return {
                "status": "out_of_scope",
                "domain_id": self.domain_id,
                "applicable": False,
                "reason": f"Sector {sector!r} is outside the banking domain pack.",
            }
        return {"status": "applicable", "domain_id": self.domain_id, "applicable": True, "sector": sector}

    def envelope(self, requirements: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_scope": "banking_network_architecture_and_technical_controls_only",
            "scope_guard": self.guard_domain(requirements),
            "artifact": artifact,
            "integration_targets": dict(self.integration_targets),
            "decisions": list(self.decisions),
            "assumptions": list(self.assumptions),
            "source_of_truth": requirements.get("source_of_truth", "requirements_document"),
            "compliance_claim": "not_certified_by_domain_pack",
        }

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.envelope(requirements, {})
