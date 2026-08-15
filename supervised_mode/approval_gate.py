"""Human approval gate for supervised checkpoints."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from governance import CheckpointRecord, CheckpointType, SignoffPolicy

from .supervision_context import SupervisionContext, SupervisionContextManager, SupervisionEvent
from .supervision_policy import SupervisionPolicyEvaluation
from .workflow_mode import SupervisionDecision, WorkflowStage


class ApprovalGateResult(BaseModel):
    """Outcome of an approval gate evaluation."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    decision: SupervisionDecision
    continued: bool
    human_intervention: bool
    approver_id: str | None = None
    approver_role: str | None = None
    approval_reference: str = ""
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


class ApprovalGate:
    """Require a named, referenceable human approval before continuation."""

    def __init__(self, *, signoff_policy: SignoffPolicy | None = None, context_manager: SupervisionContextManager | None = None) -> None:
        """Initialize approval gate with governance and context integrations."""
        self.signoff_policy = signoff_policy or SignoffPolicy()
        self.context_manager = context_manager or SupervisionContextManager()

    def evaluate(self, evaluation: SupervisionPolicyEvaluation, context: SupervisionContext, *, approver_id: str | None = None, approver_role: str | None = None, approval_reference: str = "", action: str = "", rationale: str = "", evidence_ids: Iterable[str] = ()) -> tuple[SupervisionContext, ApprovalGateResult]:
        """Record approval or leave the checkpoint awaiting an approver."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if evaluation.decision == SupervisionDecision.BLOCKED:
            return context, ApprovalGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.BLOCKED, continued=False, human_intervention=False, reasons=evaluation.reasons, evidence_ids=evidence)
        if evaluation.decision == SupervisionDecision.AUTO_CONTINUE:
            return context, ApprovalGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.AUTO_CONTINUE, continued=True, human_intervention=False, reasons=evaluation.reasons, evidence_ids=evidence)
        if evaluation.decision != SupervisionDecision.REQUIRES_APPROVAL:
            return context, ApprovalGateResult(checkpoint_id=evaluation.checkpoint_id, decision=evaluation.decision, continued=False, human_intervention=False, reasons=("approval gate received a checkpoint requiring a different gate",), evidence_ids=evidence)
        if not approver_id or not approver_role or not approval_reference or not action:
            return context, ApprovalGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.REQUIRES_APPROVAL, continued=False, human_intervention=True, reasons=("human approval and approval:// reference are required",), approval_reference=approval_reference, evidence_ids=evidence)
        if not approval_reference.startswith("approval://"):
            raise ValueError("approval reference must use approval:// scheme")
        if not rationale.strip():
            raise ValueError("approver rationale is mandatory")
        outcome = "accepted" if action in {"approve", "approved", "continue"} else "deferred"
        record = CheckpointRecord(checkpoint_id=evaluation.checkpoint_id, workflow=evaluation.workflow_stage, checkpoint_type=CheckpointType.APPROVAL, principal_id=approver_id, role=approver_role, outcome=outcome, rationale=rationale, reference=approval_reference, evidence_ids=evidence)
        recorded = self.signoff_policy.record_checkpoint(record)
        decision = SupervisionDecision.AUTO_CONTINUE if recorded.outcome.value == "accepted" else SupervisionDecision.REQUIRES_APPROVAL
        event = SupervisionEvent(event_id=f"approval:{evaluation.checkpoint_id}:{approver_id}", checkpoint_id=evaluation.checkpoint_id, workflow_stage=WorkflowStage(evaluation.workflow_stage), decision=decision, actor_id=approver_id, actor_role=approver_role, action=action, rationale=rationale, reference=approval_reference, evidence_ids=evidence)
        updated = self.context_manager.append_event(context, event)
        result = ApprovalGateResult(checkpoint_id=evaluation.checkpoint_id, decision=decision, continued=decision == SupervisionDecision.AUTO_CONTINUE, human_intervention=True, approver_id=approver_id, approver_role=approver_role, approval_reference=approval_reference, reasons=("approval accepted" if decision == SupervisionDecision.AUTO_CONTINUE else "approval deferred",), evidence_ids=evidence)
        return updated, result
