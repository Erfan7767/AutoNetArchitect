"""Serializable state machine for phased execution."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class ExecutionState:
    """Mutable execution state with explicit phase status."""
    completed_phases: list[int] = field(default_factory=list)
    current_phase: int | None = None
    file_registry: dict[str, dict[str, Any]] = field(default_factory=dict)
    pending_items: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    def complete(self, phase_id: int) -> None:
        """Mark a phase complete exactly once."""
        if phase_id not in self.completed_phases: self.completed_phases.append(phase_id)
        self.current_phase = None
    def to_dict(self) -> dict[str, Any]:
        """Return serializable state."""
        return asdict(self)
