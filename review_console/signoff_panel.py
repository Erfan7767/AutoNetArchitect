"""Presentation adapter for governance sign-off state."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner


class SignoffPanelView(BaseModel):
    """Governance sign-off state shown in the console."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    allowed: bool
    state: str
    required_reviews: tuple[str, ...] = ()
    completed_reviews: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    completed_approvals: tuple[str, ...] = ()
    required_accountability: str | None = None
    completed_accountability: str | None = None
    required_execution_authority: tuple[str, ...] = ()
    completed_execution_authority: tuple[str, ...] = ()
    pending_checkpoints: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    decision_reference: str = ""


class SignoffPanel(BaseDesigner):
    """Render SignoffEvaluation and delegate actions to governance services."""

    def __init__(self) -> None:
        """Initialize sign-off panel."""
        super().__init__("SignoffPanel")
        self.record_decision("signoff_panel_policy", "display_and_delegate", "console renders governance evaluation and does not approve or record checkpoints itself")

    def build(self, evaluation: Any | None) -> SignoffPanelView | None:
        """Build a view from an existing SignoffEvaluation."""
        if evaluation is None:
            return None
        data = evaluation if isinstance(evaluation, dict) else dict(evaluation.model_dump()) if hasattr(evaluation, "model_dump") else {}
        return SignoffPanelView(workflow=str(data.get("workflow", "unknown")), allowed=bool(data.get("allowed", False)), state=str(data.get("state", "unknown")), required_reviews=tuple(str(value) for value in data.get("required_reviews", ())), completed_reviews=tuple(str(value) for value in data.get("completed_reviews", ())), required_approvals=tuple(str(value) for value in data.get("required_approvals", ())), completed_approvals=tuple(str(value) for value in data.get("completed_approvals", ())), required_accountability=data.get("required_accountability"), completed_accountability=data.get("completed_accountability"), required_execution_authority=tuple(str(value) for value in data.get("required_execution_authority", ())), completed_execution_authority=tuple(str(value) for value in data.get("completed_execution_authority", ())), pending_checkpoints=tuple(str(value) for value in data.get("pending_checkpoints", ())), reasons=tuple(str(value) for value in data.get("reasons", ())), evidence_ids=tuple(str(value) for value in data.get("evidence_ids", ())), decision_reference=str(data.get("decision_reference", "")))
