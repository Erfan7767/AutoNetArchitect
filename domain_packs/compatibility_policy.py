from __future__ import annotations

from typing import Any

from .domain_pack_registry import DomainPackRegistry


class CompatibilityPolicy:
    """Enforce limited inheritance and prevent incompatible production packs."""

    def __init__(self, registry: DomainPackRegistry | None = None) -> None:
        self.registry = registry or DomainPackRegistry()

    def evaluate(self, active_packs: list[str], general_rules: dict[str, Any] | None = None, sector_rules: dict[str, Any] | None = None, governance_rules: dict[str, Any] | None = None, compliance_rules: dict[str, Any] | None = None) -> dict[str, Any]:
        general = general_rules or {}
        sector = sector_rules or {}
        governance = governance_rules or {}
        compliance = compliance_rules or {}
        unknown = [pack for pack in active_packs if self.registry.get(pack) is None]
        conflicts = []
        for index, left in enumerate(active_packs):
            record = self.registry.get(left)
            if record is None:
                continue
            for right in active_packs[index + 1:]:
                if right in record.incompatible_with:
                    conflicts.append({"left": left, "right": right, "reason": "registered sector packs are mutually exclusive for one production workflow"})
        inheritance = {
            "general_to_sector": "allowed_additive_or_stricter_only",
            "sector_to_general": "not_allowed",
            "governance_override": "may_block_or_require_review_but_may_not_weaken_security",
            "compliance_override": "requires_authoritative_evidence_and_scope",
        }
        weakening = bool(sector.get("weakens_general_controls") or governance.get("weakens_security") or compliance.get("unscoped_claim"))
        status = "blocked" if unknown or conflicts or weakening else "compatible"
        return {"status": status, "active_packs": list(active_packs), "unknown_packs": unknown, "conflicts": conflicts, "inheritance_policy": inheritance, "rule_precedence": ["general_minimum", "sector_stricter_controls", "governance_gates", "compliance_evidence"], "weakening_detected": weakening, "general_rules_present": bool(general), "sector_rules_present": bool(sector), "governance_rules_present": bool(governance), "compliance_rules_present": bool(compliance)}
