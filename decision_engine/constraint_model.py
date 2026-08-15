"""Hard and soft constraint models."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
@dataclass(frozen=True)
class ConstraintResult:
    """Constraint evaluation result."""
    constraint_id: str
    satisfied: bool
    penalty: float = 0.0
    reason: str = ""
@dataclass(frozen=True)
class Constraint:
    """A hard rejection or soft penalty rule."""
    constraint_id: str
    kind: str
    check: Callable[[Any], bool]
    penalty: float = 0.0
    description: str = ""
    def __post_init__(self) -> None:
        if self.kind not in {"hard", "soft"} or self.penalty < 0: raise ValueError("invalid constraint")
    def evaluate(self, alternative: Any) -> ConstraintResult:
        """Evaluate the constraint against an alternative."""
        ok = bool(self.check(alternative)); return ConstraintResult(self.constraint_id, ok, 0.0 if ok else self.penalty, self.description)
