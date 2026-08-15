"""Primary workflow coordination contracts for AutoNetArchitect.

This module contains no user-interface code.  It provides immutable-enough
workflow records, explicit stage ordering, strict precondition evaluation,
and guarded Source of Truth transitions for higher-level entry points.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Callable, Mapping

from audit.audit_trail import AuditTrail
from source_of_truth.sot_manager import SoTManager, SoTNotFoundError, SoTConflictError, SoTRecord, SoTType


class OrchestratorError(RuntimeError):
    """Base error for workflow orchestration failures."""


class StageOrderError(OrchestratorError):
    """Raised when a workflow attempts to skip or repeat a stage."""


class PreconditionError(OrchestratorError):
    """Raised when a required workflow precondition is not satisfied."""


class SoTTransitionError(OrchestratorError):
    """Raised when a Source of Truth transition is missing or conflicting."""


class WorkflowStage(str, Enum):
    """Canonical lifecycle stages in their only permitted order."""

    QUESTIONNAIRE = "questionnaire"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    EQUIPMENT = "equipment"
    CONFIG_GENERATION = "config_generation"
    DEPLOYMENT_PREPARATION = "deployment_preparation"
    DEPLOYMENT_EXECUTION = "deployment_execution"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    REPORTS = "reports"


STAGE_ORDER: tuple[WorkflowStage, ...] = tuple(WorkflowStage)


@dataclass(frozen=True)
class Preconditions:
    """Explicit facts required before a stage can be entered."""

    project_valid: bool = True
    unresolved_human_inputs: tuple[str, ...] = ()
    required_evidence_ids: tuple[str, ...] = ()
    required_approval_references: tuple[str, ...] = ()
    required_sot_types: tuple[str, ...] = ()
    required_sot_record_ids: tuple[str, ...] = ()
    allow_preview: bool = False


@dataclass
class WorkflowContext:
    """Mutable workflow state owned by the orchestration boundary."""

    workflow_id: str
    project_id: str
    actor: str
    current_stage: str
    completed_stages: tuple[str, ...] = ()
    sot_records: dict[str, str] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    approval_references: tuple[str, ...] = ()
    unresolved_human_inputs: tuple[str, ...] = ()
    project_valid: bool = True
    supervised_mode: bool = True
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize and validate workflow identity fields."""
        if not self.workflow_id or not self.project_id or not self.actor:
            raise ValueError("workflow_id, project_id, and actor are required")
        self.current_stage = WorkflowStage(self.current_stage).value
        normalized_completed = tuple(WorkflowStage(item).value for item in self.completed_stages)
        self.completed_stages = normalized_completed
        self.evidence_ids = tuple(str(item) for item in self.evidence_ids)
        self.approval_references = tuple(str(item) for item in self.approval_references)
        self.unresolved_human_inputs = tuple(str(item) for item in self.unresolved_human_inputs)
        if self.correlation_id is None:
            self.correlation_id = self.workflow_id

    def next_stage(self) -> WorkflowStage:
        """Return the only legal next stage."""
        current = WorkflowStage(self.current_stage)
        index = STAGE_ORDER.index(current)
        if index + 1 >= len(STAGE_ORDER):
            raise StageOrderError("workflow is already at the terminal stage")
        return STAGE_ORDER[index + 1]

    def can_enter(self, target: WorkflowStage | str) -> bool:
        """Return whether target is exactly the next stage."""
        return self.next_stage() == WorkflowStage(target)

    def apply_transition(self, target: WorkflowStage | str) -> None:
        """Advance the context by exactly one canonical stage."""
        normalized = WorkflowStage(target)
        if not self.can_enter(normalized):
            raise StageOrderError(f"cannot transition from {self.current_stage} to {normalized.value}")
        self.completed_stages = self.completed_stages + (normalized.value,)
        self.current_stage = normalized.value

    def attach_sot(self, record: SoTRecord) -> None:
        """Attach one registered record to the workflow context."""
        self.sot_records[record.sot_type] = record.record_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize the context without secret values."""
        return {
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "actor": self.actor,
            "current_stage": self.current_stage,
            "completed_stages": list(self.completed_stages),
            "sot_records": dict(self.sot_records),
            "evidence_ids": list(self.evidence_ids),
            "approval_references": list(self.approval_references),
            "unresolved_human_inputs": list(self.unresolved_human_inputs),
            "project_valid": self.project_valid,
            "supervised_mode": self.supervised_mode,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkflowContext":
        """Reconstruct a context from a serialized mapping."""
        if not isinstance(payload, Mapping):
            raise ValueError("workflow context must be a mapping")
        return cls(
            workflow_id=str(payload["workflow_id"]),
            project_id=str(payload["project_id"]),
            actor=str(payload["actor"]),
            current_stage=str(payload["current_stage"]),
            completed_stages=tuple(str(item) for item in payload.get("completed_stages", ())),
            sot_records={str(key): str(value) for key, value in dict(payload.get("sot_records", {})).items()},
            evidence_ids=tuple(str(item) for item in payload.get("evidence_ids", ())),
            approval_references=tuple(str(item) for item in payload.get("approval_references", ())),
            unresolved_human_inputs=tuple(str(item) for item in payload.get("unresolved_human_inputs", ())),
            project_valid=bool(payload.get("project_valid", True)),
            supervised_mode=bool(payload.get("supervised_mode", True)),
            correlation_id=str(payload["correlation_id"]) if payload.get("correlation_id") else None,
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class OrchestratorResult:
    """Secret-safe result returned by every orchestrator entry point."""

    result_id: str
    workflow_id: str
    project_id: str
    stage: str
    status: str
    success: bool
    reasons: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    sot_record_id: str | None = None
    audit_entry_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result as a JSON-safe mapping."""
        return {
            "result_id": self.result_id,
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "stage": self.stage,
            "status": self.status,
            "success": self.success,
            "reasons": list(self.reasons),
            "artifact_ids": list(self.artifact_ids),
            "sot_record_id": self.sot_record_id,
            "audit_entry_id": self.audit_entry_id,
            "data": dict(self.data),
            "generated_at": self.generated_at,
        }


StageHandler = Callable[[WorkflowContext, Mapping[str, Any]], Mapping[str, Any]]


class MasterOrchestrator:
    """Coordinate lifecycle state, preconditions, SoT transitions, and audit."""

    def __init__(self, *, sot_manager: SoTManager, audit_trail: AuditTrail | None = None) -> None:
        """Create a master orchestrator with explicit persistence dependencies."""
        self.sot_manager = sot_manager
        self.audit_trail = audit_trail

    def create_context(self, *, project_id: str, actor: str, completed_through: WorkflowStage | str = WorkflowStage.QUESTIONNAIRE, workflow_id: str | None = None, evidence_ids: tuple[str, ...] = (), approval_references: tuple[str, ...] = (), unresolved_human_inputs: tuple[str, ...] = (), project_valid: bool = True, supervised_mode: bool = True, metadata: Mapping[str, Any] | None = None) -> WorkflowContext:
        """Create a contiguous context whose completed stages are explicit."""
        if not project_id or not actor:
            raise ValueError("project_id and actor are required")
        terminal = WorkflowStage(completed_through)
        index = STAGE_ORDER.index(terminal)
        completed = tuple(item.value for item in STAGE_ORDER[: index + 1])
        return WorkflowContext(
            workflow_id=workflow_id or f"workflow:{uuid.uuid4()}",
            project_id=project_id,
            actor=actor,
            current_stage=terminal.value,
            completed_stages=completed,
            evidence_ids=evidence_ids,
            approval_references=approval_references,
            unresolved_human_inputs=unresolved_human_inputs,
            project_valid=project_valid,
            supervised_mode=supervised_mode,
            metadata=dict(metadata or {}),
        )

    def validate_preconditions(self, context: WorkflowContext, *, target_stage: WorkflowStage | str, preconditions: Preconditions) -> tuple[str, ...]:
        """Return all blocking reasons without mutating workflow state."""
        target = WorkflowStage(target_stage)
        reasons: list[str] = []
        if not context.can_enter(target):
            reasons.append(f"stage order violation: current={context.current_stage}, target={target.value}")
        if not context.project_valid or not preconditions.project_valid:
            reasons.append("project state is invalid")
        unresolved = tuple(dict.fromkeys(context.unresolved_human_inputs + preconditions.unresolved_human_inputs))
        if unresolved:
            reasons.append("unresolved HumanSuppliedMandatory inputs affect the requested stage")
        missing_evidence = tuple(item for item in preconditions.required_evidence_ids if item not in context.evidence_ids)
        if missing_evidence:
            reasons.append(f"required evidence is missing: {', '.join(missing_evidence)}")
        missing_approvals = tuple(item for item in preconditions.required_approval_references if item not in context.approval_references)
        if missing_approvals:
            reasons.append(f"required approval references are missing: {', '.join(missing_approvals)}")
        for sot_type in preconditions.required_sot_types:
            normalized = SoTType(sot_type).value
            record_id = context.sot_records.get(normalized)
            if record_id is None:
                reasons.append(f"required SoT record is not attached: {normalized}")
                continue
            try:
                self.sot_manager.authoritative(normalized, record_id)
            except (SoTNotFoundError, SoTConflictError, ValueError) as exc:
                reasons.append(f"required authoritative SoT is unavailable for {normalized}: {exc}")
        for record_id in preconditions.required_sot_record_ids:
            try:
                record = self.sot_manager.get(record_id)
                if not record.approved:
                    reasons.append(f"required SoT record is not approved: {record_id}")
            except SoTNotFoundError:
                reasons.append(f"required SoT record is missing: {record_id}")
        return tuple(dict.fromkeys(reasons))

    def require_preconditions(self, context: WorkflowContext, *, target_stage: WorkflowStage | str, preconditions: Preconditions) -> None:
        """Raise a typed error when any strict precondition fails."""
        reasons = self.validate_preconditions(context, target_stage=target_stage, preconditions=preconditions)
        if reasons:
            raise PreconditionError("; ".join(reasons))

    def register_transition_sot(self, context: WorkflowContext, *, sot_type: SoTType | str, payload: Mapping[str, Any], source: str, authority: str, evidence_ids: tuple[str, ...] = (), approval_reference: str | None = None) -> SoTRecord:
        """Register a transition record and approve only with explicit approval evidence."""
        if not payload:
            raise SoTTransitionError("transition payload must not be empty")
        if not source or not authority:
            raise SoTTransitionError("SoT source and authority are required")
        normalized_evidence = tuple(dict.fromkeys(evidence_ids))
        if not normalized_evidence and approval_reference is not None:
            raise SoTTransitionError("approval cannot be recorded without evidence IDs")
        record = self.sot_manager.register(
            sot_type=sot_type,
            payload=dict(payload),
            authority=authority,
            source=source,
            evidence_ids=normalized_evidence,
            approved=approval_reference is not None,
        )
        context.attach_sot(record)
        context.metadata.setdefault("approval_references_by_sot", {})[record.sot_type] = approval_reference
        self._audit_transition(context, record, approval_reference)
        return record

    def advance(self, context: WorkflowContext, target_stage: WorkflowStage | str, *, artifact_ids: tuple[str, ...] = (), data: Mapping[str, Any] | None = None, reasons: tuple[str, ...] = (), sot_record_id: str | None = None) -> OrchestratorResult:
        """Advance one stage and emit a secret-safe audit record."""
        target = WorkflowStage(target_stage)
        context.apply_transition(target)
        audit_id = self._audit_stage(context, target, "completed", reasons)
        return OrchestratorResult(
            result_id=f"result:{uuid.uuid4()}",
            workflow_id=context.workflow_id,
            project_id=context.project_id,
            stage=target.value,
            status="completed",
            success=True,
            reasons=reasons,
            artifact_ids=artifact_ids,
            sot_record_id=sot_record_id,
            audit_entry_id=audit_id,
            data=dict(data or {}),
        )

    def blocked(self, context: WorkflowContext, *, stage: WorkflowStage | str, reasons: tuple[str, ...]) -> OrchestratorResult:
        """Return and audit a blocked result without mutating stage state."""
        normalized = tuple(dict.fromkeys(reason for reason in reasons if reason))
        audit_id = self._audit_stage(context, WorkflowStage(stage), "blocked", normalized)
        return OrchestratorResult(
            result_id=f"result:{uuid.uuid4()}",
            workflow_id=context.workflow_id,
            project_id=context.project_id,
            stage=WorkflowStage(stage).value,
            status="blocked",
            success=False,
            reasons=normalized,
            audit_entry_id=audit_id,
        )

    def execute_stage(self, context: WorkflowContext, *, target_stage: WorkflowStage | str, preconditions: Preconditions, handler: StageHandler, input_data: Mapping[str, Any]) -> OrchestratorResult:
        """Validate, invoke an injected business service, and advance the stage."""
        target = WorkflowStage(target_stage)
        reasons = self.validate_preconditions(context, target_stage=target, preconditions=preconditions)
        if reasons:
            return self.blocked(context, stage=target, reasons=reasons)
        if not callable(handler):
            return self.blocked(context, stage=target, reasons=("stage handler is not callable",))
        try:
            output = dict(handler(context, input_data))
        except Exception as exc:
            return self.blocked(context, stage=target, reasons=(f"stage handler failed: {type(exc).__name__}: {exc}",))
        if not output:
            return self.blocked(context, stage=target, reasons=("stage handler returned no artifact data",))
        return self.advance(context, target, data=output, artifact_ids=tuple(str(item) for item in output.get("artifact_ids", ())))

    def _audit_transition(self, context: WorkflowContext, record: SoTRecord, approval_reference: str | None) -> None:
        """Record an SoT transition without payload contents."""
        if self.audit_trail is None:
            return
        self.audit_trail.record(
            "orchestrator.sot_transition",
            context.actor,
            {
                "workflow_id": context.workflow_id,
                "project_id": context.project_id,
                "sot_type": record.sot_type,
                "record_id": record.record_id,
                "version": record.version,
                "approved": record.approved,
                "approval_reference_present": approval_reference is not None,
                "evidence_ids": list(record.evidence_ids),
            },
            outcome="approved" if record.approved else "registered",
            source="orchestrators.master_orchestrator",
            correlation_id=context.correlation_id,
        )

    def _audit_stage(self, context: WorkflowContext, stage: WorkflowStage, outcome: str, reasons: tuple[str, ...]) -> str | None:
        """Record a stage decision and return its audit identifier."""
        if self.audit_trail is None:
            return None
        entry = self.audit_trail.record(
            "orchestrator.stage_transition",
            context.actor,
            {
                "workflow_id": context.workflow_id,
                "project_id": context.project_id,
                "current_stage": context.current_stage,
                "target_stage": stage.value,
                "completed_stages": list(context.completed_stages),
                "outcome": outcome,
                "reasons": list(reasons),
                "sot_record_types": sorted(context.sot_records),
            },
            outcome=outcome,
            source="orchestrators.master_orchestrator",
            correlation_id=context.correlation_id,
        )
        return entry.entry_id

    def run_design(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), approval_reference: str | None = None) -> OrchestratorResult:
        """Delegate design execution to the dedicated design orchestrator."""
        from .design_orchestrator import DesignOrchestrator
        return DesignOrchestrator(master=self).run(context, input_data, handler=handler, evidence_ids=evidence_ids, approval_reference=approval_reference)

    def prepare_deployment(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), approval_reference: str | None = None) -> OrchestratorResult:
        """Delegate deployment preparation to the dedicated deployment orchestrator."""
        from .deployment_orchestrator import DeploymentOrchestrator
        return DeploymentOrchestrator(master=self).prepare(context, input_data, handler=handler, evidence_ids=evidence_ids, approval_reference=approval_reference)

    def execute_deployment(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), real_execution: bool = False) -> OrchestratorResult:
        """Delegate deployment execution to the dedicated deployment orchestrator."""
        from .deployment_orchestrator import DeploymentOrchestrator
        return DeploymentOrchestrator(master=self).execute(context, input_data, handler=handler, evidence_ids=evidence_ids, real_execution=real_execution)

    def run_operations(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), mutating: bool = False) -> OrchestratorResult:
        """Delegate operations execution to the dedicated operations orchestrator."""
        from .operations_orchestrator import OperationsOrchestrator
        return OperationsOrchestrator(master=self).run(context, input_data, handler=handler, evidence_ids=evidence_ids, mutating=mutating)
