"""Contradiction detection for questionnaire answers."""
from __future__ import annotations
from pydantic import BaseModel
from .constraint_rules import ConstraintRules, ConstraintViolation
class ContradictionReport(BaseModel):
    """Bilingual contradiction report."""
    contradictions: list[ConstraintViolation] = []
    @property
    def has_contradictions(self) -> bool:
        """Return whether contradictions exist."""
        return bool(self.contradictions)
class ContradictionDetector:
    """Detect semantic contradictions using registered rules."""
    def __init__(self, rules: ConstraintRules | None = None) -> None: self.rules = rules or ConstraintRules()
    def detect(self, answers: dict[str, object]) -> ContradictionReport:
        """Evaluate answers and return a report."""
        return ContradictionReport(contradictions=self.rules.evaluate(answers))
