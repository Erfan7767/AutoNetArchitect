"""Explicit abstention and no-decision policy."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class AbstentionDecision:
    """First-class no-decision outcome."""
    status: str
    reasons: list[str]
    required_information: list[str]
class AbstentionPolicy:
    """Decide when evidence is insufficient for a recommendation."""
    def assess(self, missing_information: list[str], alternatives: list[object], confidence: float, threshold: float) -> AbstentionDecision | None:
        """Return no-decision when required evidence or confidence is insufficient."""
        reasons = []; if_missing = bool(missing_information);
        if if_missing: reasons.append("required information is missing")
        if len(alternatives) < 2: reasons.append("fewer than two competing alternatives")
        if confidence < threshold: reasons.append("confidence is below decision threshold")
        return AbstentionDecision("no_decision", reasons, missing_information) if reasons else None
