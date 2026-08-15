"""Presentation adapter for unresolved review items."""
from __future__ import annotations

from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class UnresolvedCategory(str, Enum):
    """Required unresolved-item categories."""

    HUMAN_SUPPLIED_MANDATORY = "human_supplied_mandatory"
    ASSUMPTION = "assumption"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SCOPE_BOUNDARY = "scope_boundary"


class UnresolvedItemView(BaseModel):
    """One unresolved item requiring engineer attention."""

    model_config = ConfigDict(extra="forbid")

    item_id: str
    category: UnresolvedCategory
    description: str
    affected_artifacts: tuple[str, ...] = ()
    required_action: str = ""
    source_reference: str = ""
    severity: str = "medium"
    resolved: bool = False


class UnresolvedViewer(BaseDesigner):
    """Collect unresolved information without inventing missing values."""

    def __init__(self) -> None:
        """Initialize unresolved viewer."""
        super().__init__("UnresolvedViewer")
        self.record_decision("unresolved_view_policy", "missing_inputs_explicit", "console displays unresolved items as supplied by source services and never fills them implicitly")

    def build(self, *, human_mandatory: Iterable[Any] = (), assumptions: Iterable[Any] = (), insufficient_evidence: Iterable[Any] = (), scope_issues: Iterable[Any] = ()) -> tuple[UnresolvedItemView, ...]:
        """Build categorized unresolved-item views."""
        rows: list[UnresolvedItemView] = []
        rows.extend(self._convert(UnresolvedCategory.HUMAN_SUPPLIED_MANDATORY, human_mandatory, "supply required human input"))
        rows.extend(self._convert(UnresolvedCategory.ASSUMPTION, assumptions, "validate or explicitly accept assumption"))
        rows.extend(self._convert(UnresolvedCategory.INSUFFICIENT_EVIDENCE, insufficient_evidence, "collect traceable evidence"))
        rows.extend(self._convert(UnresolvedCategory.SCOPE_BOUNDARY, scope_issues, "resolve scope, use preview-only path, or obtain human decision"))
        return tuple(rows)

    @staticmethod
    def _convert(category: UnresolvedCategory, items: Iterable[Any], default_action: str) -> list[UnresolvedItemView]:
        """Convert source items into a display model."""
        rows: list[UnresolvedItemView] = []
        for index, item in enumerate(items):
            data = item if isinstance(item, dict) else dict(item.model_dump()) if hasattr(item, "model_dump") else {"description": str(item)}
            rows.append(UnresolvedItemView(item_id=str(data.get("item_id", data.get("key", f"{category.value}:{index}"))), category=category, description=str(data.get("description", data.get("reason", data.get("rationale", "not supplied")))), affected_artifacts=tuple(str(value) for value in data.get("affected_artifacts", data.get("artifacts", ()))), required_action=str(data.get("required_action", data.get("resolution", default_action))), source_reference=str(data.get("source_reference", data.get("reference", ""))), severity=str(data.get("severity", "medium")), resolved=bool(data.get("resolved", False))))
        return rows
