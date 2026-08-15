"""Decision quality classification."""
from __future__ import annotations
class DecisionQuality:
    """Assess determinism, evidence, assumptions, and blocking."""
    def assess(self, result: object, evidence: list[str], assumptions: list[str], missing_information: list[str]) -> dict[str, object]:
        """Return transparent quality dimensions."""
        status = getattr(result, "status", "no_decision"); return {"deterministic": status == "decided" and not assumptions, "evidence_backed": bool(evidence), "assumption_heavy": len(assumptions) > len(evidence), "blocked": status == "no_decision" or bool(missing_information), "status": status}
