"""Scoring records for multi-objective decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass(frozen=True)
class ObjectiveScore:
    """Normalized objective score."""
    objective: str
    raw_value: float
    normalized_value: float
    weighted_value: float
@dataclass
class AlternativeScore:
    """Complete score and constraint results for an alternative."""
    alternative_name: str
    objective_scores: list[ObjectiveScore] = field(default_factory=list)
    constraint_results: list[object] = field(default_factory=list)
    total_score: float = 0.0
    rejected: bool = False
    rejection_reasons: list[str] = field(default_factory=list)
