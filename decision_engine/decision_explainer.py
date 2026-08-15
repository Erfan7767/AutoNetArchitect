"""Decision explanation generation."""
from __future__ import annotations
from typing import Any
class DecisionExplainer:
    """Produce transparent rationale and rejection reasons."""
    def explain(self, chosen: Any, scores: list[Any], evidence: list[str], confidence: float, confidence_rationale: str, status: str = "decided") -> dict[str, Any]:
        """Return chosen option, alternatives, impacts, evidence, and confidence rationale."""
        rejected = [{"option": s.alternative_name, "score": s.total_score, "rejection_reasons": s.rejection_reasons} for s in scores if s.alternative_name != getattr(chosen, "name", chosen)]
        return {"status": status, "chosen_option": getattr(chosen, "name", chosen) if chosen else None, "rejected_options": rejected, "constraint_impacts": [{"option": s.alternative_name, "constraints": [getattr(c, "__dict__", str(c)) for c in s.constraint_results]} for s in scores], "evidence_basis": evidence, "confidence": confidence, "confidence_rationale": confidence_rationale, "rationale": "highest admissible weighted utility with explicit constraint and evidence accounting"}
