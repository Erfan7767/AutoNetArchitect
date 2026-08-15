"""Operations lifecycle orchestration with read-only-by-default controls."""
from __future__ import annotations

from typing import Any, Mapping

from source_of_truth.sot_manager import SoTType

from .master_orchestrator import MasterOrchestrator, OrchestratorResult, Preconditions, StageHandler, WorkflowContext, WorkflowStage


class OperationsOrchestrator:
    """Coordinate monitoring, health, drift, backup, and maintenance services."""

    def __init__(self, *, master: MasterOrchestrator) -> None:
        """Create an operations orchestrator without embedding service business logic."""
        self.master = master

    def run(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), mutating: bool = False) -> OrchestratorResult:
        """Run an operations service through a strict operational SoT transition."""
        data = dict(input_data)
        context.evidence_ids = tuple(dict.fromkeys(context.evidence_ids + tuple(evidence_ids)))
        required_approvals = ("operations_change_approval",) if mutating else ()
        preconditions = Preconditions(
            project_valid=bool(data.get("project_valid", context.project_valid)),
            unresolved_human_inputs=tuple(str(item) for item in data.get("unresolved_human_inputs", ())),
            required_evidence_ids=tuple(str(item) for item in data.get("required_evidence_ids", ())),
            required_approval_references=required_approvals,
            required_sot_types=(SoTType.DEPLOYMENT.value,),
        )
        reasons = list(self.master.validate_preconditions(context, target_stage=WorkflowStage.OPERATIONS, preconditions=preconditions))
        if mutating and bool(data.get("high_risk", False)) and not bool(data.get("high_risk_approval", False)):
            reasons.append("high-risk operational mutation requires explicit approval")
        if reasons:
            return self.master.blocked(context, stage=WorkflowStage.OPERATIONS, reasons=tuple(dict.fromkeys(reasons)))
        effective_handler = handler or self._default_handler
        try:
            output = dict(effective_handler(context, data))
        except Exception as exc:
            return self.master.blocked(context, stage=WorkflowStage.OPERATIONS, reasons=(f"operations service failed: {type(exc).__name__}: {exc}",))
        artifact_ids = tuple(str(item) for item in output.get("artifact_ids", ()))
        if not output or not artifact_ids:
            return self.master.blocked(context, stage=WorkflowStage.OPERATIONS, reasons=("operations service did not return evidence artifact IDs",))
        try:
            record = self.master.register_transition_sot(
                context,
                sot_type=SoTType.OPERATIONAL,
                payload={
                    "project_id": context.project_id,
                    "workflow_id": context.workflow_id,
                    "artifact_ids": list(artifact_ids),
                    "mode": "mutating" if mutating else "read_only",
                    "service": str(data.get("service", "operations_service")),
                },
                source=str(data.get("source", "operations_orchestrator")),
                authority=str(data.get("authority", context.actor)),
                evidence_ids=context.evidence_ids,
                approval_reference=str(data.get("approval_reference")) if data.get("approval_reference") else None,
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            return self.master.blocked(context, stage=WorkflowStage.OPERATIONS, reasons=(f"operational SoT transition failed: {exc}",))
        return self.master.advance(
            context,
            WorkflowStage.OPERATIONS,
            artifact_ids=artifact_ids,
            data=output | {"sot_record_id": record.record_id, "sot_approved": record.approved, "mode": "mutating" if mutating else "read_only"},
            sot_record_id=record.record_id,
        )

    @staticmethod
    def _default_handler(context: WorkflowContext, input_data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Accept externally collected operational evidence."""
        artifact = input_data.get("operational_artifact_id") or input_data.get("artifact_id")
        if not artifact:
            return {}
        return {"artifact_ids": (str(artifact),), "service": str(input_data.get("service", "external_operations_service"))}
