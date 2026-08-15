"""Real questionnaire constraint rules."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
@dataclass(frozen=True)
class ConstraintViolation:
    """A failed cross-field constraint."""
    rule_id: str
    message_en: str
    message_ar: str
    fields: tuple[str, ...]
@dataclass(frozen=True)
class ConstraintRule:
    """Callable cross-field rule."""
    rule_id: str
    check: Callable[[dict[str, Any]], bool]
    message_en: str
    message_ar: str
    fields: tuple[str, ...]
class ConstraintRules:
    """Evaluate network requirements constraints."""
    def __init__(self) -> None:
        self.rules = [
            ConstraintRule("users_positive", lambda d: d.get("expected_users", 1) > 0, "Expected users must be positive", "عدد المستخدمين المتوقع يجب أن يكون موجبًا", ("expected_users",)),
            ConstraintRule("sites_for_wan", lambda d: not d.get("wan_required", False) or d.get("site_count", 0) >= 2, "WAN requires at least two sites", "تطلب شبكة WAN موقعين على الأقل", ("wan_required", "site_count")),
            ConstraintRule("ha_capacity", lambda d: not d.get("high_availability", False) or d.get("redundancy_level", 0) >= 1, "High availability requires redundancy", "التوافر العالي يتطلب تكرارًا", ("high_availability", "redundancy_level")),
            ConstraintRule("greenfield_inventory", lambda d: d.get("environment_type") != "greenfield" or not d.get("existing_inventory_required", False), "Greenfield cannot require existing inventory", "لا يجوز أن يطلب greenfield جردًا قائمًا", ("environment_type", "existing_inventory_required")),
        ]
    def evaluate(self, data: dict[str, Any]) -> list[ConstraintViolation]:
        """Return all violated rules."""
        return [ConstraintViolation(r.rule_id, r.message_en, r.message_ar, r.fields) for r in self.rules if not r.check(data)]
