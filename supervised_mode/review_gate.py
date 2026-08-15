"""Human review gate for supervised checkpoints."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from governance import CheckpointRecord, CheckpointType, SignoffPolicy

from .supervision_context import SupervisionContext, SupervisionContextManager, SupervisionEvent
from .supervision_policy import SupervisionPolicyEvaluation
from .workflow_mode import SupervisionDecision, WorkflowStage


class ReviewGateResult(BaseModel):
    """Outcome of a review gate evaluation."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    decision: SupervisionDecision
    continued: bool
    human_intervention: bool
    reviewer_id: str | None = None
    reviewer_role: str | None = None
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


class ReviewGate:
    """Require a human review for a requires-review policy decision."""

    def __init__(self, *, signoff_policy: SignoffPolicy | None = None, context_manager: SupervisionContextManager | None = None) -> None:
        """Initialize review gate with governance and context integrations."""
        self.signoff_policy = signoff_policy or SignoffPolicy()
        self.context_manager = context_manager or SupervisionContextManager()

    def evaluate(self, evaluation: SupervisionPolicyEvaluation, context: SupervisionContext, *, reviewer_id: str | None = None, reviewer_role: str | None = None, action: str = "", rationale: str = "", reference: str = "", evidence_ids: Iterable[str] = ()) -> tuple[SupervisionContext, ReviewGateResult]:
        """Record review or leave the checkpoint awaiting a reviewer."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if evaluation.decision == SupervisionDecision.BLOCKED:
            result = ReviewGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.BLOCKED, continued=False, human_intervention=False, reasons=evaluation.reasons, evidence_ids=evidence)
            return context, result
        if evaluation.decision == SupervisionDecision.AUTO_CONTINUE:
            result = ReviewGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.AUTO_CONTINUE, continued=True, human_intervention=False, reasons=evaluation.reasons, evidence_ids=evidence)
            return context, result
        if evaluation.decision != SupervisionDecision.REQUIRES_REVIEW:
            result = ReviewGateResult(checkpoint_id=evaluation.checkpoint_id, decision=evaluation.decision, continued=False, human_intervention=False, reasons=("review gate received a checkpoint requiring a different gate",), evidence_ids=evidence)
            return context, result
        if not reviewer_id or not reviewer_role or not action:
            result = ReviewGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.REQUIRES_REVIEW, continued=False, human_intervention=True, reasons=("human reviewer action is required",), evidence_ids=evidence)
            return context, result
        if not rationale.strip():
            raise ValueError("reviewer rationale is mandatory")
        record = CheckpointRecord(checkpoint_id=evaluation.checkpoint_id, workflow=evaluation.workflow_stage, checkpoint_type=CheckpointType.REVIEW, principal_id=reviewer_id, role=reviewer_role, outcome="accepted" if action in {"accept", "accepted", "continue"} else "deferred", rationale=rationale, reference=reference, evidence_ids=evidence)
        recorded = self.signoff_policy.record_checkpoint(record)
        event = SupervisionEvent(event_id=f"review:{evaluation.checkpoint_id}:{reviewer_id}", checkpoint_id=evaluation.checkpoint_id, workflow_stage=WorkflowStage(evaluation.workflow_stage), decision=SupervisionDecision.AUTO_CONTINUE if recorded.outcome.value == "accepted" else SupervisionDecision.REQUIRES_REVIEW, actor_id=reviewer_id, actor_role=reviewer_role, action=action, rationale=rationale, reference=reference, evidence_ids=evidence)
        updated = self.context_manager.append_event(context, event)
        result = ReviewGateResult(checkpoint_id=evaluation.checkpoint_id, decision=event.decision, continued=event.decision == SupervisionDecision.AUTO_CONTINUE, human_intervention=True, reviewer_id=reviewer_id, reviewer_role=reviewer_role, reasons=("review accepted" if event.decision == SupervisionDecision.AUTO_CONTINUE else "review deferred",), evidence_ids=evidence)
        return updated, result
