"""Decision policy for supervised checkpoints."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner

from .checkpoint_registry import CheckpointDefinition, CheckpointRegistry
from .supervision_context import SupervisionContext
from .workflow_mode import SupervisionDecision, WorkflowMode


class SupervisionPolicyEvaluation(BaseModel):
    """Explainable decision returned for one checkpoint."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    workflow_stage: str
    decision: SupervisionDecision
    allowed_actions: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    required_human_role: str
    block_conditions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


class SupervisionPolicy(BaseDesigner):
    """Evaluate checkpoint policy without inferring human decisions."""

    def __init__(self, registry: CheckpointRegistry | None = None) -> None:
        """Initialize policy with the full checkpoint registry."""
        super().__init__("SupervisionPolicy")
        self.registry = registry or CheckpointRegistry()
        self.record_decision("supervision_default", "deny_autonomy", "policy returns explicit checkpoint decisions and never auto-approves a human gate")

    def evaluate(self, checkpoint_id: str, context: SupervisionContext, *, evidence_ids: Iterable[str] = (), active_conditions: Iterable[str] = (), mutating: bool = False) -> SupervisionPolicyEvaluation:
        """Evaluate one registered checkpoint against context and conditions."""
        definition = self.registry.get(checkpoint_id)
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        conditions = {str(item).strip() for item in active_conditions if str(item).strip()}
        reasons: list[str] = []
        decision = definition.decision_type
        if context.mode in {WorkflowMode.READ_ONLY, WorkflowMode.PREVIEW} and mutating:
            decision = SupervisionDecision.BLOCKED
            reasons.append(f"workflow mode {context.mode.value} does not permit mutating execution")
        if definition.evidence_required and not evidence and decision == SupervisionDecision.AUTO_CONTINUE:
            reasons.append("no evidence supplied; checkpoint remains under explicit review")
            decision = SupervisionDecision.REQUIRES_REVIEW
        violated = tuple(item for item in definition.block_conditions if item in conditions)
        if violated:
            decision = SupervisionDecision.BLOCKED
            reasons.extend(f"block condition active: {item}" for item in violated)
        if decision in {SupervisionDecision.REQUIRES_REVIEW, SupervisionDecision.REQUIRES_APPROVAL} and not context.has_human_owner():
            reasons.append("named human owner is missing from supervision context")
            if decision == SupervisionDecision.REQUIRES_APPROVAL:
                decision = SupervisionDecision.BLOCKED
        if decision == SupervisionDecision.AUTO_CONTINUE:
            reasons.append("policy permits bounded non-mutating continuation")
        self.record_decision(f"evaluate:{checkpoint_id}", decision.value, "checkpoint outcome is determined by registered policy, mode, evidence, and explicit conditions")
        return SupervisionPolicyEvaluation(checkpoint_id=checkpoint_id, workflow_stage=definition.workflow_stage.value, decision=decision, allowed_actions=definition.allowed_actions, reasons=tuple(dict.fromkeys(reasons)), required_human_role=definition.required_human_role, block_conditions=definition.block_conditions, evidence_ids=evidence)

    def definition_for_stage(self, stage: str) -> tuple[CheckpointDefinition, ...]:
        """Return policy definitions for a stage."""
        return self.registry.for_stage(stage)
