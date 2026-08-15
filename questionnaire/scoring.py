"""Questionnaire completeness and confidence scoring."""
from __future__ import annotations
class ScoringEngine:
    """Score completeness, confirmation, and consistency."""
    def score(self, required_fields: list[str], answers: dict[str, object], contradictions: int = 0) -> float:
        """Return a score from zero to one."""
        if not required_fields: return 1.0
        filled = sum(1 for field in required_fields if answers.get(field) not in (None, ""))
        return max(0.0, min(1.0, filled / len(required_fields) - contradictions * 0.1))
