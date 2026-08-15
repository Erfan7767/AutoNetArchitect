"""Production readiness gate integrated with proof and governance evidence."""
from __future__ import annotations

from typing import Iterable

from governance import SignoffEvaluation
from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .go_no_go_engine import GoNoGoEngine
from .mandatory_checkpoints import CheckpointRecord
from .no_go_policy import BlockerClass, NoGoBlocker, NoGoEvaluation, NoGoOutcome


class ReadinessAssessment(BaseModel):
    """Explainable production readiness assessment."""

    model_config = ConfigDict(extra="forbid")

    stage: str
    production_ready: bool
    readiness_status: str
    no_go_evaluation: NoGoEvaluation
    proof_status: str
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    governance_reference: str = ""


class ReadinessGate(BaseDesigner):
    """Prevent production readiness claims without evidence and governance."""

    def __init__(self, *, engine: GoNoGoEngine | None = None) -> None:
        """Initialize readiness gate."""
        super().__init__("ReadinessGate")
        self.engine = engine or GoNoGoEngine()
        self.record_decision("readiness_default", "not_production_ready_without_proof_and_governance", "production readiness requires evidence, resolved blockers, and human governance")

    def assess(self, *, stage: str, checkpoint_records: Iterable[CheckpointRecord] = (), blockers: Iterable[NoGoBlocker] = (), proof_status: str = "not_verifiable_with_current_inputs", evidence_ids: Iterable[str] = (), field_feasibility_status: str = "not_supplied", governance_evaluation: SignoffEvaluation | None = None, production_requested: bool = True, approval_present: bool = False, governance_reference: str = "") -> ReadinessAssessment:
        """Assess production readiness without turning unknown evidence into readiness."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        blocker_items = list(blockers)
        reasons: list[str] = []
        actions: list[str] = []
        if proof_status in {"failed", "not_verifiable_with_current_inputs", ""}:
            blocker_items.append(NoGoBlocker(blocker_id=f"readiness:proof:{stage}", blocker_class=BlockerClass.VERIFICATION, blocking_reason=f"proof status is {proof_status or 'not supplied'}", affected_stage=stage, required_resolution="supply valid verification evidence and repeat the relevant proof", evidence_ids=evidence))
            reasons.append("proof status does not support production readiness")
            actions.append("complete formal or evidence-backed verification")
        if field_feasibility_status in {"blocked_pending_site_data", "blocked_due_to_constraints", "not_supplied"}:
            blocker_items.append(NoGoBlocker(blocker_id=f"readiness:field:{stage}", blocker_class=BlockerClass.DESIGN, blocking_reason=f"field feasibility status is {field_feasibility_status}", affected_stage=stage, required_resolution="complete field feasibility review and resolve site constraints", evidence_ids=evidence))
            reasons.append("field execution feasibility is not cleared")
            actions.append("resolve field feasibility state")
        if governance_evaluation is not None and not governance_evaluation.allowed:
            blocker_items.append(NoGoBlocker(blocker_id=f"readiness:governance:{stage}", blocker_class=BlockerClass.GOVERNANCE, blocking_reason="governance sign-off evaluation is not allowed", affected_stage=stage, required_resolution="complete required human review, approval, accountability, and execution authority checkpoints", evidence_ids=governance_evaluation.evidence_ids))
            reasons.append("governance sign-off is incomplete")
            actions.append("complete governance checkpoints")
        evaluation = self.engine.evaluate(stage=stage, checkpoint_records=checkpoint_records, blockers=blocker_items, production_requested=production_requested, approval_present=approval_present, governance_reference=governance_reference)
        ready = evaluation.outcome == NoGoOutcome.GO and evaluation.production_release_allowed and not reasons
        status = "production_ready" if ready else "blocked_no_go" if evaluation.outcome == NoGoOutcome.NO_GO else "pending_review"
        if not ready:
            actions.extend(evaluation.reasons)
        self.record_decision(f"readiness:{stage}", status, "readiness is bounded by proof status, field feasibility, governance, checkpoints, and no-go blockers")
        return ReadinessAssessment(stage=stage, production_ready=ready, readiness_status=status, no_go_evaluation=evaluation, proof_status=proof_status, evidence_ids=evidence, reasons=tuple(dict.fromkeys(reasons + list(evaluation.reasons))), required_actions=tuple(dict.fromkeys(actions)), governance_reference=governance_reference)
