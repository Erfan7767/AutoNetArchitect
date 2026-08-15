from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner


class EnterpriseDomainBase(BaseDesigner):
    """Shared auditable contract for the Enterprise Corporate domain pack."""

    domain_id = "enterprise_corporate"
    supported_sector_values = {"enterprise_corporate", "corporate_enterprise"}

    integration_targets = {
        "requirements": "requirements.requirements_analyzer.RequirementsAnalyzer",
        "design": "designers",
        "equipment": "equipment_selector",
        "compliance": "compliance",
    }

    def guard_domain(self, requirements: dict[str, Any]) -> dict[str, Any]:
        sector = requirements.get("sector", requirements.get("organization_type"))
        if sector is None:
            self.record_assumption(
                "sector",
                self.domain_id,
                "The caller did not provide a sector; this pack remains opt-in and is not applied implicitly.",
            )
            return {
                "status": "sector_required",
                "domain_id": self.domain_id,
                "applicable": False,
                "reason": "Explicit enterprise_corporate sector selection is required.",
            }
        applicable = str(sector).lower() in self.supported_sector_values
        if not applicable:
            self.record_decision(
                "domain_scope_guard",
                "rejected",
                "Enterprise Corporate pack cannot be generalized to another sector.",
                alternatives=["select_sector_specific_domain_pack"],
                rejection_reasons={"requested_sector": f"{sector} is outside enterprise_corporate scope"},
            )
            return {
                "status": "out_of_scope",
                "domain_id": self.domain_id,
                "applicable": False,
                "reason": f"Sector {sector!r} is outside this domain pack.",
            }
        return {
            "status": "applicable",
            "domain_id": self.domain_id,
            "applicable": True,
            "sector": sector,
        }

    def envelope(self, requirements: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        return {
            "domain_id": self.domain_id,
            "domain_scope": "enterprise_corporate_only",
            "scope_guard": guard,
            "artifact": artifact,
            "integration_targets": dict(self.integration_targets),
            "decisions": list(self.decisions),
            "assumptions": list(self.assumptions),
            "source_of_truth": requirements.get("source_of_truth", "requirements_document"),
        }

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.envelope(requirements, {})
