"""Evidence-bounded confidence and fidelity evaluation for Digital Twins."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .twin_model import StateCertainty, TwinModel, TwinStateKind


@dataclass(frozen=True)
class TwinConfidenceReport:
    """Confidence result that separates coverage, certainty, and fidelity."""

    score: float
    level: str
    fidelity_cap: str
    state_coverage: float
    observed_state_count: int
    inferred_state_count: int
    replayed_state_count: int
    missing_state_kinds: tuple[str, ...]
    evidence_basis: tuple[str, ...]
    rationale: tuple[str, ...]
    production_safe_claim_allowed: bool = False
    full_fidelity_claim: bool = False
    limitations: tuple[str, ...] = ("confidence is bounded by supplied evidence", "digital twin output is not production change authorization")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the confidence report."""
        return asdict(self) | {"missing_state_kinds": list(self.missing_state_kinds), "evidence_basis": list(self.evidence_basis), "rationale": list(self.rationale), "limitations": list(self.limitations)}


class TwinConfidenceEvaluator:
    """Evaluate twin confidence without equating model completeness with reality."""

    DEFAULT_REQUIRED_KINDS = (TwinStateKind.LOGICAL.value, TwinStateKind.DEPLOYMENT.value, TwinStateKind.DISCOVERED.value, TwinStateKind.OPERATIONAL.value)

    def evaluate(
        self,
        twin: TwinModel,
        *,
        required_state_kinds: Sequence[str] | None = None,
        protocol_fidelity_evidence: Mapping[str, Any] | None = None,
    ) -> TwinConfidenceReport:
        """Calculate evidence-bounded confidence and a conservative fidelity claim."""
        required = tuple(required_state_kinds or self.DEFAULT_REQUIRED_KINDS)
        represented = set(twin.state_kinds())
        missing = tuple(kind for kind in required if kind not in represented)
        observed = sum(state.provenance.certainty in {StateCertainty.OBSERVED.value, StateCertainty.DECLARED.value} for state in twin.states)
        inferred = sum(state.provenance.certainty in {StateCertainty.INFERRED.value, StateCertainty.AMBIGUOUS.value} for state in twin.states)
        replayed = sum(state.provenance.certainty == StateCertainty.REPLAYED.value for state in twin.states)
        evidence_basis = tuple(sorted({evidence for state in twin.states for evidence in state.provenance.evidence_ids}))
        if not twin.states:
            return TwinConfidenceReport(0.0, "unknown", "insufficient_evidence", 0.0, 0, 0, 0, missing, evidence_basis, ("no twin states were supplied",), False, False)
        coverage = max(0.0, min(1.0, len(represented & set(required)) / max(len(required), 1)))
        weighted = sum(max(0.0, min(1.0, state.provenance.confidence)) for state in twin.states) / len(twin.states)
        certainty_penalty = (inferred * 0.12 + replayed * 0.06) / len(twin.states)
        score = max(0.0, min(0.95, (weighted * 0.65) + (coverage * 0.35) - certainty_penalty))
        full_fidelity = bool(protocol_fidelity_evidence and protocol_fidelity_evidence.get("full_fidelity") is True and protocol_fidelity_evidence.get("evidence_ids"))
        fidelity_cap = "full_fidelity_evidenced" if full_fidelity else "evidence_bounded"
        if not full_fidelity:
            score = min(score, 0.9)
        level = "high" if score >= 0.8 else "medium" if score >= 0.55 else "low" if score > 0.0 else "unknown"
        rationale = [f"state coverage is {coverage:.2f}", f"{observed} declared or observed states, {inferred} inferred states, and {replayed} replayed states were included"]
        if missing:
            rationale.append("required state kinds are missing: " + ", ".join(missing))
        if not evidence_basis:
            rationale.append("no evidence identifiers were supplied")
        if not full_fidelity:
            rationale.append("full protocol fidelity is not claimed because qualifying evidence was not supplied")
        return TwinConfidenceReport(score, level, fidelity_cap, coverage, observed, inferred, replayed, missing, evidence_basis, tuple(rationale), False, full_fidelity)
