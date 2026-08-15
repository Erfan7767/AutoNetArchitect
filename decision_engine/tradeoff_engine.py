"""Weighted multi-objective tradeoff engine."""
from __future__ import annotations
from .decision_context import DecisionContext, Alternative
from .scoring_models import AlternativeScore, ObjectiveScore
class TradeoffEngine:
    """Normalize objective values and calculate weighted utility."""
    def score(self, context: DecisionContext, alternatives: list[Alternative]) -> list[AlternativeScore]:
        """Score alternatives while preserving raw values."""
        output: list[AlternativeScore] = []
        for alternative in alternatives:
            record = AlternativeScore(alternative.name); total = 0.0
            for objective in context.objectives:
                raw = float(alternative.attributes.get(objective.name, 0.0)); normalized = raw if objective.direction == "maximize" else -raw; weighted = normalized * objective.weight; record.objective_scores.append(ObjectiveScore(objective.name, raw, normalized, weighted)); total += weighted
            record.total_score = total; output.append(record)
        return output
