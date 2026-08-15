"""Presentation adapter for decision alternatives."""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class AlternativeView(BaseModel):
    """One alternative rendered for engineer review."""

    model_config = ConfigDict(extra="forbid")

    name: str
    score: float | None = None
    selected: bool = False
    rejection_reasons: tuple[str, ...] = ()
    constraint_impacts: tuple[dict[str, Any], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


class AlternativeViewer(BaseDesigner):
    """Render alternatives from existing decision outputs."""

    def __init__(self) -> None:
        """Initialize alternative viewer."""
        super().__init__("AlternativeViewer")
        self.record_decision("alternative_view_policy", "display_source_scores", "console displays decision-engine results and does not recompute ranking")

    def build(self, *, chosen_name: str | None, ranked: Iterable[Any] = (), explanation: dict[str, Any] | None = None) -> tuple[AlternativeView, ...]:
        """Build views from ranked score objects or explainer output."""
        explanation_data = explanation or {}
        rejected_by_name = {str(item.get("option")): item for item in explanation_data.get("rejected_options", ()) if isinstance(item, dict)}
        rows: list[AlternativeView] = []
        for item in ranked:
            name = str(getattr(item, "alternative_name", getattr(item, "name", "unknown")))
            score = getattr(item, "total_score", None)
            constraint_results = getattr(item, "constraint_results", ())
            reasons = tuple(str(value) for value in getattr(item, "rejection_reasons", ()) or rejected_by_name.get(name, {}).get("rejection_reasons", ()))
            rows.append(AlternativeView(name=name, score=float(score) if isinstance(score, (float, int)) else rejected_by_name.get(name, {}).get("score"), selected=name == chosen_name, rejection_reasons=reasons, constraint_impacts=tuple(self._constraint_view(value) for value in constraint_results)))
        for name, item in rejected_by_name.items():
            if not any(row.name == name for row in rows):
                rows.append(AlternativeView(name=name, score=item.get("score"), rejection_reasons=tuple(str(value) for value in item.get("rejection_reasons", ()))))
        return tuple(rows)

    @staticmethod
    def _constraint_view(value: Any) -> dict[str, Any]:
        """Normalize an existing constraint result for display only."""
        if isinstance(value, dict):
            return dict(value)
        return {key: getattr(value, key) for key in ("constraint_id", "satisfied", "penalty", "reason") if hasattr(value, key)} or {"value": str(value)}
