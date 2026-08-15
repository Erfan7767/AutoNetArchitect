"""Deployment lifecycle orchestration above transport-specific deployment code."""
from __future__ import annotations

from typing import Any, Mapping

from source_of_truth.sot_manager import SoTType

from .master_orchestrator import MasterOrchestrator, OrchestratorResult, Preconditions, StageHandler, WorkflowContext, WorkflowStage


class DeploymentOrchestrator:
    """Coordinate deployment preparation and execution through injected services."""

    def __init__(self, *, master: MasterOrchestrator) -> None:
        """Create a deployment orchestrator with no direct UI dependency."""
        self.master = master

    def prepare(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), approval_reference: str | None = None) -> OrchestratorResult:
        """Prepare a deployment artifact and register a non-authoritative DEPLOYMENT SoT record."""
        data = dict(input_data)
        context.evidence_ids = tuple(dict.fromkeys(context.evidence_ids + tuple(evidence_ids)))
        preconditions = Preconditions(
            project_valid=bool(data.get("project_valid", context.project_valid)),
            unresolved_human_inputs=tuple(str(item) for item in data.get("unresolved_human_inputs", ())),
            required_evidence_ids=tuple(str(item) for item in data.get("required_evidence_ids", ())),
            required_sot_types=(SoTType.DESIGN.value,),
        )
        reasons = self.master.validate_preconditions(context, target_stage=WorkflowStage.DEPLOYMENT_PREPARATION, preconditions=preconditions)
        if reasons:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_PREPARATION, reasons=reasons)
        effective_handler = handler or self._default_prepare_handler
        try:
            output = dict(effective_handler(context, data))
        except Exception as exc:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_PREPARATION, reasons=(f"deployment preparation failed: {type(exc).__name__}: {exc}",))
        artifact_ids = tuple(str(item) for item in output.get("artifact_ids", ()))
        if not output or not artifact_ids:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_PREPARATION, reasons=("deployment preparation did not return artifact IDs",))
        try:
            record = self.master.register_transition_sot(
                context,
                sot_type=SoTType.DEPLOYMENT,
                payload={
                    "project_id": context.project_id,
                    "workflow_id": context.workflow_id,
                    "artifact_ids": list(artifact_ids),
                    "mode": "prepared",
                    "transport": str(data.get("transport", "unspecified")),
                },
                source=str(data.get("source", "deployment_orchestrator")),
                authority=str(data.get("authority", context.actor)),
                evidence_ids=context.evidence_ids,
                approval_reference=approval_reference,
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_PREPARATION, reasons=(f"deployment SoT transition failed: {exc}",))
        return self.master.advance(
            context,
            WorkflowStage.DEPLOYMENT_PREPARATION,
            artifact_ids=artifact_ids,
            data=output | {"sot_record_id": record.record_id, "sot_approved": record.approved},
            sot_record_id=record.record_id,
        )

    def execute(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), real_execution: bool = False) -> OrchestratorResult:
        """Execute a prepared deployment only when strict approval and backup gates are met."""
        data = dict(input_data)
        context.evidence_ids = tuple(dict.fromkeys(context.evidence_ids + tuple(evidence_ids)))
        required_approvals = ("deployment_approval",) if real_execution else ()
        required_evidence = tuple(str(item) for item in data.get("required_evidence_ids", ()))
        preconditions = Preconditions(
            project_valid=bool(data.get("project_valid", context.project_valid)),
            unresolved_human_inputs=tuple(str(item) for item in data.get("unresolved_human_inputs", ())),
            required_evidence_ids=required_evidence,
            required_approval_references=required_approvals,
            required_sot_types=(SoTType.DESIGN.value, SoTType.DEPLOYMENT.value),
        )
        reasons = list(self.master.validate_preconditions(context, target_stage=WorkflowStage.DEPLOYMENT_EXECUTION, preconditions=preconditions))
        if real_execution and not data.get("backup_reference"):
            reasons.append("real deployment requires a non-empty backup reference")
        if real_execution and bool(data.get("remote_destructive", False)) and not bool(data.get("destructive_operation_approval", False)):
            reasons.append("remote-destructive deployment requires explicit destructive-operation approval")
        if reasons:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_EXECUTION, reasons=tuple(dict.fromkeys(reasons)))
        effective_handler = handler or self._default_execute_handler
        try:
            output = dict(effective_handler(context, data))
        except Exception as exc:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_EXECUTION, reasons=(f"deployment execution failed: {type(exc).__name__}: {exc}",))
        artifact_ids = tuple(str(item) for item in output.get("artifact_ids", ()))
        if not output or not artifact_ids:
            return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_EXECUTION, reasons=("deployment service did not return execution artifact IDs",))
        return self.master.advance(
            context,
            WorkflowStage.DEPLOYMENT_EXECUTION,
            artifact_ids=artifact_ids,
            data=output | {"execution_mode": "real" if real_execution else "dry_run"},
        )

    @staticmethod
    def _default_prepare_handler(context: WorkflowContext, input_data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Accept an externally produced deployment package."""
        artifact = input_data.get("deployment_artifact_id") or input_data.get("artifact_id")
        if not artifact:
            return {}
        return {"artifact_ids": (str(artifact),), "service": "external_deployment_preparation_service"}

    @staticmethod
    def _default_execute_handler(context: WorkflowContext, input_data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Accept an externally executed deployment result without opening transports."""
        artifact = input_data.get("execution_result_id") or input_data.get("artifact_id")
        if not artifact:
            return {}
        return {"artifact_ids": (str(artifact),), "service": "external_deployment_execution_service", "state": str(input_data.get("state", "completed"))}
