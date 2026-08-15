"""Explicit blocking gate for supervised workflows."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from .supervision_context import SupervisionContext, SupervisionContextManager, SupervisionEvent
from .supervision_policy import SupervisionPolicyEvaluation
from .workflow_mode import SupervisionDecision, WorkflowStage


class BlockGateResult(BaseModel):
    """Outcome of a block gate."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    decision: SupervisionDecision
    continued: bool = False
    human_intervention: bool = False
    reasons: tuple[str, ...] = ()
    required_human_actions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


class BlockGate:
    """Convert policy violations into an explicit, auditable blocked state."""

    def __init__(self, *, context_manager: SupervisionContextManager | None = None) -> None:
        """Initialize block gate with context event integration."""
        self.context_manager = context_manager or SupervisionContextManager()

    def evaluate(self, evaluation: SupervisionPolicyEvaluation, context: SupervisionContext, *, evidence_ids: Iterable[str] = ()) -> tuple[SupervisionContext, BlockGateResult]:
        """Record block event when policy says blocked and never continue automatically."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if evaluation.decision != SupervisionDecision.BLOCKED:
            return context, BlockGateResult(checkpoint_id=evaluation.checkpoint_id, decision=evaluation.decision, continued=evaluation.decision == SupervisionDecision.AUTO_CONTINUE, reasons=("block gate was not applicable",), evidence_ids=evidence)
        event = SupervisionEvent(event_id=f"blocked:{evaluation.checkpoint_id}:{context.workflow_run_id}", checkpoint_id=evaluation.checkpoint_id, workflow_stage=WorkflowStage(evaluation.workflow_stage), decision=SupervisionDecision.BLOCKED, actor_id="system", actor_role="supervision_policy", action="", rationale="; ".join(evaluation.reasons), reference="", evidence_ids=evidence)
        updated = self.context_manager.append_event(context, event)
        result = BlockGateResult(checkpoint_id=evaluation.checkpoint_id, decision=SupervisionDecision.BLOCKED, reasons=evaluation.reasons, required_human_actions=(f"resolve:{item}" for item in evaluation.block_conditions), evidence_ids=evidence)
        return updated, result
