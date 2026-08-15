"""Execution context carried through supervised workflow stages."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from audit.audit_trail import AuditTrail
from designers.base_designer import BaseDesigner

from .workflow_mode import SupervisionDecision, WorkflowMode, WorkflowModeState, WorkflowStage


class SupervisionEvent(BaseModel):
    """Immutable-style record of one checkpoint evaluation or human action."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    checkpoint_id: str = Field(min_length=1)
    workflow_stage: WorkflowStage
    decision: SupervisionDecision
    actor_id: str = "system"
    actor_role: str = "system"
    action: str = ""
    rationale: str = ""
    reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SupervisionContext(BaseModel):
    """Explicit context that prevents a workflow from losing supervision state."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    workflow_run_id: str = Field(min_length=1)
    mode: WorkflowMode = WorkflowMode.SUPERVISED
    high_assurance: bool = True
    human_owner_id: str | None = None
    human_owner_role: str = "engineer_in_charge"
    current_stage: WorkflowStage | None = None
    events: tuple[SupervisionEvent, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    sot_basis: dict[str, str] = Field(default_factory=dict)
    audit_correlation_id: str | None = None

    def pending_events(self) -> tuple[SupervisionEvent, ...]:
        """Return events that require a human action before continuation."""
        return tuple(item for item in self.events if item.decision in {SupervisionDecision.REQUIRES_REVIEW, SupervisionDecision.REQUIRES_APPROVAL, SupervisionDecision.BLOCKED} and item.action == "")

    def has_human_owner(self) -> bool:
        """Return whether an accountable human owner is recorded."""
        return bool(self.human_owner_id and self.human_owner_role)


class SupervisionContextManager(BaseDesigner):
    """Create and update explicit supervision contexts."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize context manager with optional audit integration."""
        super().__init__("SupervisionContextManager")
        self.audit_trail = audit_trail
        self.record_decision("context_default_mode", WorkflowMode.SUPERVISED.value, "every high-assurance run starts with an explicit supervision context")

    def create(self, *, project_id: str, workflow_run_id: str, mode: WorkflowMode | str = WorkflowMode.SUPERVISED, human_owner_id: str | None = None, human_owner_role: str = "engineer_in_charge", sot_basis: dict[str, str] | None = None, audit_correlation_id: str | None = None) -> SupervisionContext:
        """Create a context and record missing owner information as an assumption."""
        selected_mode = WorkflowMode(mode)
        if selected_mode == WorkflowMode.SUPERVISED and not human_owner_id:
            self.record_assumption(f"owner:{workflow_run_id}", "not supplied", "supervised workflows need a named engineer before mutation or approval")
        context = SupervisionContext(project_id=project_id, workflow_run_id=workflow_run_id, mode=selected_mode, high_assurance=True, human_owner_id=human_owner_id, human_owner_role=human_owner_role, sot_basis=sot_basis or {}, audit_correlation_id=audit_correlation_id)
        self.record_decision(f"context:{workflow_run_id}", selected_mode.value, "supervision context is explicit and carried across stages")
        return context

    def enter_stage(self, context: SupervisionContext, stage: WorkflowStage | str) -> SupervisionContext:
        """Return context with an explicit current stage."""
        selected_stage = WorkflowStage(stage)
        updated = context.model_copy(update={"current_stage": selected_stage})
        self.record_decision(f"stage:{context.workflow_run_id}:{selected_stage.value}", "entered", "workflow stage transition is recorded explicitly")
        return updated

    def append_event(self, context: SupervisionContext, event: SupervisionEvent) -> SupervisionContext:
        """Append an event and emit a secret-safe audit record."""
        updated = context.model_copy(update={"events": context.events + (event,), "evidence_ids": tuple(dict.fromkeys(context.evidence_ids + event.evidence_ids))})
        self.record_decision(f"event:{event.event_id}", event.decision.value, "supervision event is retained for reporting and later orchestration")
        if self.audit_trail is not None:
            self.audit_trail.record("supervised_mode.checkpoint", event.actor_id, {"project_id": context.project_id, "workflow_run_id": context.workflow_run_id, "checkpoint_id": event.checkpoint_id, "workflow_stage": event.workflow_stage.value, "decision": event.decision.value, "actor_role": event.actor_role, "action": event.action, "reference": event.reference, "evidence_ids": list(event.evidence_ids)}, outcome=event.decision.value, correlation_id=context.audit_correlation_id)
        return updated
