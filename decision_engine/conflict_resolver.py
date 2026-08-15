"""Conflict resolution for competing constraints."""
from __future__ import annotations
from dataclasses import dataclass
from .constraint_model import Constraint
@dataclass(frozen=True)
class ConflictReport:
    """Detected constraint conflict."""
    conflict: bool
    constraints: list[str]
    resolution: str
class ConflictResolver:
    """Never silently override hard constraints."""
    def resolve(self, constraints: list[Constraint]) -> ConflictReport:
        """Identify conflicts that require human policy."""
        hard = [c.constraint_id for c in constraints if c.kind == "hard"]; return ConflictReport(len(hard) > 1, hard, "defer_to_human_policy" if len(hard) > 1 else "no_conflict")
