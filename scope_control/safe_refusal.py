"""Safe refusal responses for boundary violations."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class RefusalResult:
    """Structured refusal or guarded fallback."""
    status: str
    reason: str
    violated_boundary: str
    affected_workflow: str
    required_human_action: str
    preview_only_available: bool
class SafeRefusal:
    """Translate a violation into an explicit action-oriented response."""
    def refuse(self, reason: str, boundary: str, workflow: str, action: str, preview_available: bool = False, status: str = "unsupported") -> RefusalResult:
        """Return a safe refusal without silently falling through."""
        return RefusalResult(status, reason, boundary, workflow, action, preview_available)
