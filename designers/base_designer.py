"""Base classes for traceable network design decisions and assumptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DecisionRecord:
    """Auditable engineering decision."""

    designer: str
    decision_id: str
    choice: Any
    rationale: str
    alternatives: list[Any] = field(default_factory=list)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Assumption:
    """Explicit assumption with impact and validation requirement."""

    key: str
    value: Any
    rationale: str
    requires_validation: bool = True


class BaseDesigner:
    """Base class ensuring every designer records decisions and assumptions."""

    def __init__(self, name: str | None = None) -> None:
        """Create a designer with empty decision and assumption registries."""
        self.name = name or self.__class__.__name__
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def record_decision(
        self,
        decision_id: str,
        choice: Any,
        rationale: str,
        alternatives: list[Any] | None = None,
        rejection_reasons: dict[str, str] | None = None,
    ) -> DecisionRecord:
        """Record a decision before returning a design."""
        record = DecisionRecord(
            designer=self.name,
            decision_id=decision_id,
            choice=choice,
            rationale=rationale,
            alternatives=alternatives or [],
            rejection_reasons=rejection_reasons or {},
        )
        self.decisions.append(record)
        return record

    def record_assumption(
        self,
        key: str,
        value: Any,
        rationale: str,
        requires_validation: bool = True,
    ) -> Assumption:
        """Record an assumption explicitly."""
        assumption = Assumption(key, value, rationale, requires_validation)
        self.assumptions.append(assumption)
        return assumption

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Generate a design through a concrete designer implementation."""
        raise TypeError(f"a concrete designer implementation is required for {self.name}")
