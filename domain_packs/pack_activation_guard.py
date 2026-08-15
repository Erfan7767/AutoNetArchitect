from __future__ import annotations

from typing import Any

from .compatibility_policy import CompatibilityPolicy
from .domain_pack_registry import DomainPackRegistry


class PackActivationGuard:
    """Block unverified, ambiguous, or conflicting production pack activation."""

    def __init__(self, registry: DomainPackRegistry | None = None) -> None:
        self.registry = registry or DomainPackRegistry()
        self.policy = CompatibilityPolicy(self.registry)

    def check(self, context: dict[str, Any]) -> dict[str, Any]:
        active = list(context.get("active_packs", []))
        selected = context.get("selected_pack")
        confidence = float(context.get("inference_confidence", 0.0))
        review_required = bool(context.get("review_required", True))
        policy = self.policy.evaluate(active, context.get("general_rules"), context.get("sector_rules"), context.get("governance_rules"), context.get("compliance_rules"))
        reasons = []
        if not selected:
            reasons.append("no_selected_pack")
        if confidence < 0.9:
            reasons.append("sector_confidence_below_production_threshold")
        if review_required and not context.get("review_completed", False):
            reasons.append("required_review_not_completed")
        if not active and selected:
            reasons.append("selected_pack_not_in_active_packs")
        if policy["status"] != "compatible":
            reasons.append("compatibility_policy_blocked")
        status = "allowed" if not reasons else "blocked"
        return {"status": status, "production_activation": status == "allowed", "reasons": reasons, "policy": policy, "required_action": "complete_human_review_and_resolve_policy_findings" if reasons else "continue_to_governed_workflow"}
