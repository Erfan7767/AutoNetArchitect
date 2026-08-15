"""Pure approval gate presentation model for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ApprovalWidget:
    """Display model for an action requiring human approval."""

    action: str
    stage: str
    status: str
    required_role: str
    reasons: tuple[str, ...]
    approval_reference: str | None = None

    @classmethod
    def pending(cls, *, action: str, stage: str, reasons: Iterable[str], required_role: str = "engineer") -> "ApprovalWidget":
        """Create a visible pending approval state."""
        return cls(action=action, stage=stage, status="pending", required_role=required_role, reasons=tuple(str(item) for item in reasons))

    @classmethod
    def from_result(cls, result: Any, *, required_role: str = "engineer") -> "ApprovalWidget | None":
        """Create an approval widget when a result is blocked or requires approval."""
        status = str(getattr(result, "status", ""))
        if status not in {"blocked", "requires_approval", "pending_approval"}:
            return None
        return cls(action=f"{getattr(result, 'stage', 'unknown')}_action", stage=str(getattr(result, "stage", "unknown")), status=status, required_role=required_role, reasons=tuple(str(item) for item in getattr(result, "reasons", ())))

    def render(self) -> dict[str, Any]:
        """Return visible state without allowing approval mutation."""
        return {"action": self.action, "stage": self.stage, "status": self.status, "required_role": self.required_role, "reasons": list(self.reasons), "approval_reference": self.approval_reference, "approval_action": "external_governance_required"}
