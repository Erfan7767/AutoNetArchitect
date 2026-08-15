from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner


class HospitalDomainBase(BaseDesigner):
    """Auditable, opt-in contract for hospital and clinical network patterns."""

    domain_id = "hospital_clinical"
    supported_sector_values = {"hospital", "healthcare", "hospital_clinical", "clinical"}
    integration_targets = {
        "requirements": "requirements.requirements_analyzer.RequirementsAnalyzer",
        "security": "designers.security.security_designer",
        "wireless_rf": "wireless_rf.wireless_confidence_evaluator",
        "field_reality": "field_reality.field_feasibility_checker",
        "formal_verification": "formal_verification.verification_reporter.VerificationReporter",
        "equipment": "equipment_selector",
        "deployment": "deployment",
        "compliance": "compliance",
        "knowledge": "knowledge.claim_resolver.ClaimResolver",
    }

    def guard_domain(self, requirements: dict[str, Any]) -> dict[str, Any]:
        sector = requirements.get("sector", requirements.get("organization_type"))
        if sector is None:
            self.record_assumption(
                "sector",
                self.domain_id,
                "Hospital pack activation requires an explicit healthcare or clinical sector selection.",
            )
            return {"status": "sector_required", "domain_id": self.domain_id, "applicable": False, "reason": "Explicit hospital_clinical selection is required."}
        applicable = str(sector).lower() in self.supported_sector_values
        if not applicable:
            self.record_decision(
                "hospital_scope_guard",
                "rejected",
                "Clinical network patterns must not be generalized to unrelated sectors.",
                alternatives=["select_the_matching_sector_pack"],
                rejection_reasons={"requested_sector": f"{sector} is outside hospital_clinical scope"},
            )
            return {"status": "out_of_scope", "domain_id": self.domain_id, "applicable": False, "reason": f"Sector {sector!r} is outside this domain pack."}
        return {"status": "applicable", "domain_id": self.domain_id, "applicable": True, "sector": sector}

    def clinical_review(self, requirements: dict[str, Any], path: str) -> dict[str, Any]:
        supplied = requirements.get("clinical_review_evidence", {}).get(path)
        if supplied:
            return {"required": True, "status": "evidence_supplied", "path": path, "evidence": supplied}
        self.record_assumption(path, None, "Clinically sensitive network path requires documented human clinical and biomedical review.")
        return {"required": True, "status": "human_review_required", "path": path, "evidence": None}

    def envelope(self, requirements: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_scope": "hospital_clinical_network_architecture_and_technical_controls_only",
            "scope_guard": self.guard_domain(requirements),
            "artifact": artifact,
            "integration_targets": dict(self.integration_targets),
            "decisions": list(self.decisions),
            "assumptions": list(self.assumptions),
            "source_of_truth": requirements.get("source_of_truth", "requirements_document"),
            "clinical_claim": "not_provided_by_network_domain_pack",
            "medical_approval_claim": "not_provided_by_network_domain_pack",
        }

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.envelope(requirements, {})
