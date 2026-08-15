"""Decision context and alternatives."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
@dataclass(frozen=True)
class Objective:
    """A maximization or minimization objective."""
    name: str
    weight: float
    direction: str = "maximize"
    def __post_init__(self) -> None:
        if self.weight < 0 or self.direction not in {"maximize", "minimize"}: raise ValueError("invalid objective")
@dataclass(frozen=True)
class Alternative:
    """Candidate engineering option with measurable attributes."""
    name: str
    attributes: dict[str, float] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
@dataclass(frozen=True)
class DecisionContext:
    """Complete context required for a formal decision."""
    decision_type: str
    objectives: list[Objective]
    constraints: list[Any] = field(default_factory=list)
    priorities: dict[str, float] = field(default_factory=dict)
    budget_signals: dict[str, float] = field(default_factory=dict)
    operational_preferences: dict[str, Any] = field(default_factory=dict)
    compliance_requirements: list[str] = field(default_factory=list)
    risk_tolerance: str = "medium"
    growth_expectations: dict[str, float] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
