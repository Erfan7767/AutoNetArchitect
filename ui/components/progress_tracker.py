"""Pure workflow progress view model for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from orchestrators.master_orchestrator import STAGE_ORDER


@dataclass(frozen=True)
class ProgressTracker:
    """Display model for canonical AutoNetArchitect lifecycle stages."""

    stages: tuple[str, ...]
    current_stage: str
    completed_stages: tuple[str, ...]
    status: str
    reasons: tuple[str, ...]

    @classmethod
    def from_context(cls, context: Any, *, status: str = "active", reasons: Iterable[str] = ()) -> "ProgressTracker":
        """Build a tracker from a WorkflowContext-like object."""
        stages = tuple(item.value for item in STAGE_ORDER)
        return cls(stages=stages, current_stage=str(context.current_stage), completed_stages=tuple(str(item) for item in context.completed_stages), status=status, reasons=tuple(str(item) for item in reasons))

    def render(self) -> dict[str, Any]:
        """Return display data with completion flags."""
        completed = set(self.completed_stages)
        return {"stages": [{"name": stage, "completed": stage in completed, "current": stage == self.current_stage} for stage in self.stages], "status": self.status, "reasons": list(self.reasons)}
