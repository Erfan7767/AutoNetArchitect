"""Registry of supervised workflow checkpoints."""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .workflow_mode import SupervisionDecision, WorkflowStage


class CheckpointDefinition(BaseModel):
    """Policy definition for one workflow checkpoint."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1)
    workflow_stage: WorkflowStage
    trigger_condition: str = Field(min_length=1)
    required_human_role: str = Field(min_length=1)
    decision_type: SupervisionDecision
    allowed_actions: tuple[str, ...] = ()
    block_conditions: tuple[str, ...] = ()
    high_assurance: bool = True
    evidence_required: bool = True


class CheckpointRegistry(BaseDesigner):
    """Maintain a complete, queryable registry of supervised checkpoints."""

    def __init__(self, definitions: Iterable[CheckpointDefinition] | None = None) -> None:
        """Load the default stage coverage and apply explicit definitions."""
        super().__init__("CheckpointRegistry")
        self._definitions: dict[str, CheckpointDefinition] = {item.checkpoint_id: item for item in self.default_definitions()}
        for definition in definitions or ():
            self.register(definition)
        self.record_decision("checkpoint_coverage", sorted({item.workflow_stage.value for item in self._definitions.values()}), "all required lifecycle stages have explicit checkpoints")

    @staticmethod
    def default_definitions() -> tuple[CheckpointDefinition, ...]:
        """Return conservative first-class checkpoints for each requested stage."""
        return (
            CheckpointDefinition(checkpoint_id="questionnaire.input_validation", workflow_stage=WorkflowStage.QUESTIONNAIRE, trigger_condition="questionnaire submission is received", required_human_role="requirements_owner", decision_type=SupervisionDecision.AUTO_CONTINUE, allowed_actions=("validate_schema", "identify_missing_inputs"), block_conditions=("malformed submission", "missing HumanSuppliedMandatory field")),
            CheckpointDefinition(checkpoint_id="questionnaire.completion_review", workflow_stage=WorkflowStage.QUESTIONNAIRE, trigger_condition="questionnaire answers are complete or unresolved", required_human_role="requirements_owner", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_answers", "request_clarification", "record_assumption"), block_conditions=("contradictory critical answers", "unresolved mandatory input affecting design")),
            CheckpointDefinition(checkpoint_id="requirements.analysis_review", workflow_stage=WorkflowStage.REQUIREMENTS, trigger_condition="RequirementsDocument is generated", required_human_role="technical_reviewer", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_requirements", "accept_assumption", "request_revision"), block_conditions=("unresolved contradiction", "unsupported inferred requirement")),
            CheckpointDefinition(checkpoint_id="design.intent_review", workflow_stage=WorkflowStage.DESIGN, trigger_condition="non-trivial design decision is produced", required_human_role="technical_reviewer", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_decision", "compare_alternatives", "request_revision"), block_conditions=("missing evidence", "decision abstention", "scope violation")),
            CheckpointDefinition(checkpoint_id="design.production_approval", workflow_stage=WorkflowStage.DESIGN, trigger_condition="design is marked for production path", required_human_role="service_owner", decision_type=SupervisionDecision.REQUIRES_APPROVAL, allowed_actions=("approve_design", "approve_with_conditions", "reject_design"), block_conditions=("missing technical review", "failed formal verification", "blocked field feasibility")),
            CheckpointDefinition(checkpoint_id="equipment.selection_review", workflow_stage=WorkflowStage.EQUIPMENT, trigger_condition="equipment/BOM is selected", required_human_role="technical_reviewer", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_capability_evidence", "review_license_scope", "request_alternative"), block_conditions=("missing capability evidence", "unsupported production vendor", "unknown exact model path")),
            CheckpointDefinition(checkpoint_id="config.generation_review", workflow_stage=WorkflowStage.CONFIG_GENERATION, trigger_condition="DeviceConfig artifact is generated", required_human_role="technical_reviewer", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_diff", "validate_feature_guard", "approve_preview"), block_conditions=("unsupported feature", "secret value present", "missing design traceability")),
            CheckpointDefinition(checkpoint_id="deployment.preparation_gate", workflow_stage=WorkflowStage.DEPLOYMENT_PREPARATION, trigger_condition="backup, rollback, verification, and change plan are assembled", required_human_role="change_manager", decision_type=SupervisionDecision.REQUIRES_APPROVAL, allowed_actions=("approve_preparation", "request_change", "block_execution"), block_conditions=("missing backup", "missing rollback", "invalid project state", "unresolved HumanSuppliedMandatory")),
            CheckpointDefinition(checkpoint_id="deployment.execution_gate", workflow_stage=WorkflowStage.DEPLOYMENT_EXECUTION, trigger_condition="real production execution is requested", required_human_role="deployment_approver", decision_type=SupervisionDecision.REQUIRES_APPROVAL, allowed_actions=("approve_execution", "approve_with_conditions", "reject_execution"), block_conditions=("missing sign-off", "separation-of-duties conflict", "failed verification gate", "remote destructive operation blocked")),
            CheckpointDefinition(checkpoint_id="operations.read_only_monitoring", workflow_stage=WorkflowStage.OPERATIONS, trigger_condition="read-only monitoring or drift collection starts", required_human_role="operations_reviewer", decision_type=SupervisionDecision.AUTO_CONTINUE, allowed_actions=("collect_read_only_evidence", "classify_drift", "report_health"), block_conditions=("collector is not read-only", "credential scope is unsafe")),
            CheckpointDefinition(checkpoint_id="operations.remediation_gate", workflow_stage=WorkflowStage.OPERATIONS, trigger_condition="remediation or mutation is proposed", required_human_role="service_owner", decision_type=SupervisionDecision.REQUIRES_APPROVAL, allowed_actions=("approve_remediation", "request_preview", "reject_remediation"), block_conditions=("high-risk drift without approval", "unknown severity", "missing change reference")),
            CheckpointDefinition(checkpoint_id="compliance.scope_review", workflow_stage=WorkflowStage.COMPLIANCE, trigger_condition="technical compliance assessment is generated", required_human_role="compliance_reviewer", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_scope", "review_evidence", "record_gap"), block_conditions=("scope unspecified", "evidence not traceable", "certification claim requested")),
            CheckpointDefinition(checkpoint_id="reports.content_review", workflow_stage=WorkflowStage.REPORTS, trigger_condition="final report or handover pack is generated", required_human_role="document_owner", decision_type=SupervisionDecision.REQUIRES_REVIEW, allowed_actions=("review_content", "verify_redaction", "approve_distribution"), block_conditions=("secret leakage", "missing SoT basis", "missing generation timestamp")),
        )

    def register(self, definition: CheckpointDefinition) -> CheckpointDefinition:
        """Register one checkpoint definition and replace only by explicit policy action."""
        self._definitions[definition.checkpoint_id] = definition
        self.record_decision(f"checkpoint:{definition.checkpoint_id}", definition.decision_type.value, "checkpoint definition was explicitly registered")
        return definition

    def get(self, checkpoint_id: str) -> CheckpointDefinition:
        """Return one checkpoint definition."""
        return self._definitions[checkpoint_id]

    def for_stage(self, stage: WorkflowStage | str) -> tuple[CheckpointDefinition, ...]:
        """Return checkpoints for one lifecycle stage."""
        selected = WorkflowStage(stage)
        return tuple(item for item in self._definitions.values() if item.workflow_stage == selected)

    def all(self) -> tuple[CheckpointDefinition, ...]:
        """Return all definitions deterministically."""
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def stages(self) -> tuple[WorkflowStage, ...]:
        """Return covered stages in enum order."""
        return tuple(stage for stage in WorkflowStage if any(item.workflow_stage == stage for item in self._definitions.values()))
