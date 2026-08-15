"""Presentation adapter for expert override provenance."""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class OverrideView(BaseModel):
    """One override rendered for engineer review."""

    model_config = ConfigDict(extra="forbid")

    override_id: str
    target_id: str
    target_type: str
    override_type: str
    origin: str
    status: str
    actor_id: str
    actor_role: str
    reason: str
    scope: dict[str, Any] = None
    impact: str
    revalidation_status: str
    revalidation_trigger_ids: tuple[str, ...] = ()
    provenance_chain: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    rejection_reasons: tuple[str, ...] = ()


class OverridePanel(BaseDesigner):
    """Render override records and delegate new interventions to OverrideManager."""

    def __init__(self) -> None:
        """Initialize override panel."""
        super().__init__("OverridePanel")
        self.record_decision("override_panel_policy", "display_and_delegate", "console shows override provenance and never duplicates expert override validation or application")

    def build(self, overrides: Iterable[Any] = ()) -> tuple[OverrideView, ...]:
        """Build views from OverrideApplication objects or dictionaries."""
        rows: list[OverrideView] = []
        for item in overrides:
            data = item if isinstance(item, dict) else dict(item.model_dump()) if hasattr(item, "model_dump") else {}
            scope = data.get("scope") or {}
            rows.append(OverrideView(override_id=str(data.get("override_id", "unknown")), target_id=str(data.get("target_id", "unknown")), target_type=str(data.get("target_type", "unknown")), override_type=str(data.get("override_type", "unknown")), origin=str(data.get("origin", "unknown")), status=str(data.get("status", "unknown")), actor_id=str(data.get("actor_id", "unknown")), actor_role=str(data.get("actor_role", "unknown")), reason=str(data.get("reason", "not supplied")), scope=scope, impact=str(data.get("impact", "unknown")), revalidation_status=str(data.get("revalidation_status", "unknown")), revalidation_trigger_ids=tuple(str(value) for value in data.get("revalidation_trigger_ids", ())), provenance_chain=tuple(str(value) for value in data.get("provenance_chain", ())), warnings=tuple(str(value) for value in data.get("warnings", ())), rejection_reasons=tuple(str(value) for value in data.get("rejection_reasons", ()))))
        return tuple(rows)
