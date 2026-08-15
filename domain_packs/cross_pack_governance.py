from __future__ import annotations

from typing import Any

from designers.base_designer import BaseDesigner

from .compatibility_policy import CompatibilityPolicy
from .domain_pack_registry import DomainPackRegistry


class CrossPackGovernance(BaseDesigner):
    """Produce an auditable governance decision for one workflow."""

    def __init__(self, registry: DomainPackRegistry | None = None) -> None:
        super().__init__()
        self.registry = registry or DomainPackRegistry()
        self.policy = CompatibilityPolicy(self.registry)

    def govern(self, context: dict[str, Any]) -> dict[str, Any]:
        result = self.policy.evaluate(context.get("active_packs", []), context.get("general_rules"), context.get("sector_rules"), context.get("governance_rules"), context.get("compliance_rules"))
        review = bool(context.get("review_required", True)) and not bool(context.get("review_completed", False))
        status = "blocked" if result["status"] == "blocked" else "review_required" if review else "governed"
        self.record_decision("cross_pack_governance", status, "General rules are minimum controls; sector rules may add stricter controls; governance and compliance can block but cannot weaken them.", alternatives=["governed", "review_required", "blocked"], rejection_reasons={"blocked": "compatibility or control weakening finding"})
        return {"status": status, "policy": result, "review_required": review, "decisions": list(self.decisions), "source_of_truth": context.get("source_of_truth", "requirements_document"), "evidence_ids": list(context.get("evidence_ids", []))}

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        return self.govern(requirements)
