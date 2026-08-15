"""Presentation adapter for decision and readiness risks."""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class RiskItemView(BaseModel):
    """One risk or blocker visible to the engineer."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str
    category: str
    severity: str
    description: str
    affected_stage: str = ""
    mitigation: str = ""
    source_reference: str = ""
    resolved: bool = False


class RiskViewer(BaseDesigner):
    """Collect risks from existing pack/readiness/no-go structures."""

    def __init__(self) -> None:
        """Initialize risk viewer."""
        super().__init__("RiskViewer")
        self.record_decision("risk_view_policy", "source_risk_display", "console surfaces risk inputs and does not calculate production safety itself")

    def build(self, *, risks: Iterable[Any] = (), blockers: Iterable[Any] = (), readiness: Any | None = None) -> tuple[RiskItemView, ...]:
        """Build risk views from risk dictionaries/models, blockers, and readiness reasons."""
        rows: list[RiskItemView] = []
        for index, item in enumerate(risks):
            data = self._data(item)
            rows.append(RiskItemView(risk_id=str(data.get("risk_id", f"risk:{index}")), category=str(data.get("category", "unknown")), severity=str(data.get("severity", "unknown")), description=str(data.get("description", data.get("reason", "not supplied"))), affected_stage=str(data.get("affected_stage", "")), mitigation=str(data.get("mitigation", data.get("required_resolution", ""))), source_reference=str(data.get("source_reference", "")), resolved=bool(data.get("resolved", False))))
        for index, item in enumerate(blockers):
            data = self._data(item)
            rows.append(RiskItemView(risk_id=str(data.get("blocker_id", f"blocker:{index}")), category=str(data.get("blocker_class", "blocker")), severity="blocking", description=str(data.get("blocking_reason", "not supplied")), affected_stage=str(data.get("affected_stage", "")), mitigation=str(data.get("required_resolution", "")), source_reference=str(data.get("resolution_reference", "")), resolved=bool(data.get("resolved", False))))
        if readiness is not None:
            data = self._data(readiness)
            reasons = tuple(data.get("reasons", ()))
            for index, reason in enumerate(reasons):
                rows.append(RiskItemView(risk_id=f"readiness:{index}", category="readiness", severity="high", description=str(reason), affected_stage=str(data.get("stage", "")), mitigation="; ".join(str(value) for value in data.get("required_actions", ())), source_reference=str(data.get("governance_reference", "")), resolved=False))
        return tuple(rows)

    @staticmethod
    def _data(item: Any) -> dict[str, Any]:
        """Normalize compatible models and dictionaries."""
        if isinstance(item, dict):
            return item
        if hasattr(item, "model_dump"):
            return dict(item.model_dump())
        return {key: getattr(item, key) for key in ("risk_id", "category", "severity", "description", "reason", "affected_stage", "required_resolution", "resolved") if hasattr(item, key)}
