"""Conservative classification of change type, category, and priority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeCategory, ChangePriority, ChangeRequest, ChangeType


@dataclass(frozen=True)
class ChangeClassification:
    """Classification suggestion with explanatory evidence."""

    suggested_type: str
    suggested_category: str
    suggested_priority: str
    rationale: tuple[str, ...]
    matched_standard_catalog_id: str = ""
    human_override_applied: bool = False
    decision_record: DecisionRecord | None = None
    assumption_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize classification result."""
        return asdict(self) | {"decision_record": self.decision_record.__dict__ if self.decision_record else None, "rationale": list(self.rationale), "assumption_keys": list(self.assumption_keys)}


class ChangeClassifier:
    """Suggest classification from explicit scope and business signals."""

    def classify(
        self,
        request: ChangeRequest,
        *,
        standard_catalog_id: str = "",
        production_environment: bool = True,
        urgent_restoration: bool = False,
        active_security_incident: bool = False,
        regulatory_deadline: bool = False,
        business_impact: str = "medium",
        urgency: str = "medium",
        affected_user_count: int | None = None,
        human_override: Mapping[str, str] | None = None,
    ) -> ChangeClassification:
        """Classify a request without silently overriding missing human signals."""
        reasons: list[str] = []
        assumptions: list[Assumption] = []
        device_count = len(request.affected_devices)
        if urgent_restoration or active_security_incident or regulatory_deadline:
            suggested_type = ChangeType.EMERGENCY.value
            reasons.append("urgent restoration, active security incident, or immediate regulatory deadline was explicitly supplied")
        elif standard_catalog_id and device_count <= 1 and not request.affected_services:
            suggested_type = ChangeType.STANDARD.value
            reasons.append(f"request matches standard catalog entry {standard_catalog_id}")
        else:
            suggested_type = ChangeType.NORMAL.value
            reasons.append("request does not meet the bounded standard or emergency criteria")
        category = self._category(request)
        priority = self._priority(business_impact, urgency, affected_user_count, device_count)
        if not production_environment:
            reasons.append("non-production environment lowers the classification pressure but does not remove review requirements")
        else:
            reasons.append("production environment requires normal or emergency governance unless a valid standard entry applies")
        if affected_user_count is None:
            assumptions.append(Assumption("affected_user_count", "unknown", "priority is calculated without a fabricated user count", True))
        override_applied = False
        if human_override:
            if "change_type" in human_override:
                suggested_type = human_override["change_type"]
                override_applied = True
            if "change_category" in human_override:
                category = human_override["change_category"]
                override_applied = True
            if "priority" in human_override:
                priority = human_override["priority"]
                override_applied = True
            reasons.append("human classification override was recorded and remains reviewable")
        if suggested_type not in {item.value for item in ChangeType} or category not in {item.value for item in ChangeCategory} or priority not in {item.value for item in ChangePriority}:
            raise ValueError("classification override contains an unsupported enum value")
        decision = DecisionRecord("ChangeClassifier", f"{request.change_id}:classification", {"type": suggested_type, "category": category, "priority": priority}, ["automatic_classification", "human_override"], {"automatic_classification": "bounded signals were used", "human_override": "not selected" if not override_applied else "override selected by requester"})
        request.change_type = suggested_type
        request.change_category = category
        request.priority = priority
        request.decision_records.append(decision)
        request.assumptions.extend(assumptions)
        return ChangeClassification(suggested_type, category, priority, tuple(reasons), standard_catalog_id, override_applied, decision, tuple(item.key for item in assumptions))

    @staticmethod
    def _category(request: ChangeRequest) -> str:
        """Select category from explicit config and scope metadata."""
        if request.change_category in {item.value for item in ChangeCategory} and request.change_category != ChangeCategory.CONFIGURATION.value:
            return request.change_category
        if request.config_changes:
            return ChangeCategory.CONFIGURATION.value
        return request.change_category or ChangeCategory.CONFIGURATION.value

    @staticmethod
    def _priority(business_impact: str, urgency: str, user_count: int | None, device_count: int) -> str:
        """Map explicit business signals to a conservative priority."""
        impact = str(business_impact).lower()
        urgent = str(urgency).lower()
        if impact in {"critical", "major"} or urgent in {"critical", "immediate"}:
            return ChangePriority.CRITICAL.value
        if impact in {"high", "major"} or urgent in {"high", "urgent"} or (user_count is not None and user_count > 1000) or device_count > 10:
            return ChangePriority.HIGH.value
        if impact in {"low", "minor"} and urgent in {"low", "planned"}:
            return ChangePriority.LOW.value
        return ChangePriority.MEDIUM.value
