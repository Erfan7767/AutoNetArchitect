"""Design-stage orchestration with strict lifecycle and SoT controls."""
from __future__ import annotations

from typing import Any, Mapping

from source_of_truth.sot_manager import SoTType

from .master_orchestrator import MasterOrchestrator, OrchestratorResult, Preconditions, StageHandler, WorkflowContext, WorkflowStage


class DesignOrchestrator:
    """Coordinate design services without duplicating designer business logic."""

    def __init__(self, *, master: MasterOrchestrator) -> None:
        """Create a design orchestrator using a master-owned boundary."""
        self.master = master

    def run(self, context: WorkflowContext, input_data: Mapping[str, Any], *, handler: StageHandler | None = None, evidence_ids: tuple[str, ...] = (), approval_reference: str | None = None) -> OrchestratorResult:
        """Run the design stage and create a DESIGN SoT record when artifacts exist."""
        supplied_evidence = tuple(dict.fromkeys(context.evidence_ids + tuple(evidence_ids)))
        data = dict(input_data)
        required_evidence = tuple(str(item) for item in data.get("required_evidence_ids", ()))
        required_approvals = ("design_approval",) if bool(data.get("approval_required", False)) else ()
        preconditions = Preconditions(
            project_valid=bool(data.get("project_valid", context.project_valid)),
            unresolved_human_inputs=tuple(str(item) for item in data.get("unresolved_human_inputs", ())),
            required_evidence_ids=required_evidence,
            required_approval_references=required_approvals,
            required_sot_types=(SoTType.DESIGN.value,) if bool(data.get("design_dependency_required", False)) else (),
        )
        original_evidence = context.evidence_ids
        context.evidence_ids = supplied_evidence
        try:
            reasons = self.master.validate_preconditions(context, target_stage=WorkflowStage.DESIGN, preconditions=preconditions)
            if reasons:
                return self.master.blocked(context, stage=WorkflowStage.DESIGN, reasons=reasons)
            effective_handler = handler or self._default_handler
            output = dict(effective_handler(context, data))
            if not output:
                return self.master.blocked(context, stage=WorkflowStage.DESIGN, reasons=("design service returned no artifact data",))
            artifact_ids = tuple(str(item) for item in output.get("artifact_ids", ()))
            if not artifact_ids:
                return self.master.blocked(context, stage=WorkflowStage.DESIGN, reasons=("design output does not identify an artifact",))
            record = self.master.register_transition_sot(
                context,
                sot_type=SoTType.DESIGN,
                payload={
                    "project_id": context.project_id,
                    "workflow_id": context.workflow_id,
                    "artifact_ids": list(artifact_ids),
                    "decision_ids": [str(item) for item in output.get("decision_ids", ())],
                    "approval_required": bool(data.get("approval_required", False)),
                },
                source=str(data.get("source", "design_orchestrator")),
                authority=str(data.get("authority", context.actor)),
                evidence_ids=supplied_evidence,
                approval_reference=approval_reference,
            )
            result = self.master.advance(
                context,
                WorkflowStage.DESIGN,
                artifact_ids=artifact_ids,
                data=output | {"sot_record_id": record.record_id, "sot_approved": record.approved},
                sot_record_id=record.record_id,
            )
            return result
        except (ValueError, TypeError) as exc:
            return self.master.blocked(context, stage=WorkflowStage.DESIGN, reasons=(f"design orchestration input error: {exc}",))
        finally:
            context.evidence_ids = supplied_evidence if supplied_evidence else original_evidence

    @staticmethod
    def _default_handler(context: WorkflowContext, input_data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Accept an externally produced design artifact without generating design logic."""
        artifact_id = input_data.get("artifact_id") or input_data.get("design_artifact_id")
        if not artifact_id:
            return {}
        return {
            "artifact_ids": (str(artifact_id),),
            "decision_ids": tuple(str(item) for item in input_data.get("decision_ids", ())),
            "service": "external_design_service",
        }
