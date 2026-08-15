"""Formal optimization and decision result."""
from __future__ import annotations
from dataclasses import dataclass, field
from .decision_context import DecisionContext, Alternative
from .constraint_model import Constraint
from .tradeoff_engine import TradeoffEngine
from .abstention_policy import AbstentionPolicy
from .confidence_governor import ConfidenceGovernor
from .decision_explainer import DecisionExplainer
@dataclass
class DecisionResult:
    """First-class decision or no-decision result."""
    status: str
    chosen: Alternative | None
    ranked: list[object] = field(default_factory=list)
    explanation: dict[str, object] = field(default_factory=dict)
    confidence: float = 0.0
class OptimizationEngine:
    """Reject hard violations, penalize soft violations, then rank alternatives."""
    def __init__(self) -> None: self.tradeoffs = TradeoffEngine(); self.abstention = AbstentionPolicy(); self.governor = ConfidenceGovernor(); self.explainer = DecisionExplainer()
    def decide(self, context: DecisionContext, alternatives: list[Alternative], constraints: list[Constraint] | None = None, confidence: float = 0.0) -> DecisionResult:
        """Make an explainable decision or abstain explicitly."""
        constraints = constraints if constraints is not None else list(context.constraints); scores = self.tradeoffs.score(context, alternatives)
        for score, alternative in zip(scores, alternatives):
            results = [constraint.evaluate(alternative) for constraint in constraints]; score.constraint_results = results; score.total_score -= sum(r.penalty for r in results if not r.satisfied and next(c for c in constraints if c.constraint_id == r.constraint_id).kind == "soft")
            for result in results:
                owner = next(c for c in constraints if c.constraint_id == result.constraint_id)
                if owner.kind == "hard" and not result.satisfied: score.rejected = True; score.rejection_reasons.append(result.reason or owner.description)
        admissible = [a for a, s in zip(alternatives, scores) if not s.rejected]; ranked = sorted(zip(admissible, [s for s in scores if not s.rejected]), key=lambda pair: pair[1].total_score, reverse=True); abstention = self.abstention.assess(context.missing_information, alternatives, confidence, self.governor.threshold(context.decision_type))
        if abstention or not ranked:
            reasons = abstention.reasons if abstention else ["all alternatives violate hard constraints"]; explanation = self.explainer.explain(None, scores, context.evidence, confidence, "; ".join(reasons), "no_decision"); return DecisionResult("no_decision", None, scores, explanation, confidence)
        chosen = ranked[0][0]; explanation = self.explainer.explain(chosen, scores, context.evidence, confidence, "confidence meets the configured threshold", "decided"); return DecisionResult("decided", chosen, scores, explanation, confidence)
