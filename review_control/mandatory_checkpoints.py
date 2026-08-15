"""Formal mandatory review checkpoint definitions."""
from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class CheckpointControlType(str, Enum):
    """Control behavior at a mandatory checkpoint."""

    REVIEW_ONLY = "review_only"
    APPROVAL_REQUIRED = "approval_required"
    NO_GO_UNTIL_RESOLVED = "no_go_until_resolved"


class MandatoryCheckpointStatus(str, Enum):
    """Checkpoint lifecycle status."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MandatoryCheckpointDefinition(BaseModel):
    """Definition of a checkpoint that a stage release cannot silently skip."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1)
    workflow_stage: str = Field(min_length=1)
    trigger_condition: str = Field(min_length=1)
    required_human_role: str = Field(min_length=1)
    control_type: CheckpointControlType
    required_evidence: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    block_conditions: tuple[str, ...] = ()
    release_targets: tuple[str, ...] = ()
    high_assurance: bool = True


class CheckpointRecord(BaseModel):
    """Recorded review state for one mandatory checkpoint."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    workflow_stage: str
    status: MandatoryCheckpointStatus = MandatoryCheckpointStatus.PENDING
    reviewer_id: str = ""
    reviewer_role: str = ""
    decision_reference: str = ""
    rationale: str = ""
    evidence_ids: tuple[str, ...] = ()
    blocker_ids: tuple[str, ...] = ()

    def is_release_ready(self, definition: MandatoryCheckpointDefinition) -> bool:
        """Return whether this record satisfies its control type."""
        if self.status in {MandatoryCheckpointStatus.REJECTED, MandatoryCheckpointStatus.EXPIRED}:
            return False
        if definition.control_type == CheckpointControlType.REVIEW_ONLY:
            return self.status in {MandatoryCheckpointStatus.REVIEWED, MandatoryCheckpointStatus.APPROVED, MandatoryCheckpointStatus.RESOLVED}
        if definition.control_type == CheckpointControlType.APPROVAL_REQUIRED:
            return self.status in {MandatoryCheckpointStatus.APPROVED, MandatoryCheckpointStatus.RESOLVED} and bool(self.decision_reference)
        return self.status == MandatoryCheckpointStatus.RESOLVED and not self.blocker_ids


class MandatoryCheckpointRegistry(BaseDesigner):
    """Registry of mandatory checkpoints with no implicit release path."""

    def __init__(self, definitions: Iterable[MandatoryCheckpointDefinition] | None = None) -> None:
        """Load requested default checkpoints and explicit additions."""
        super().__init__("MandatoryCheckpointRegistry")
        self._definitions: dict[str, MandatoryCheckpointDefinition] = {item.checkpoint_id: item for item in self.default_definitions()}
        for definition in definitions or ():
            self.register(definition)
        self.record_decision("mandatory_checkpoint_coverage", sorted(self._definitions), "mandatory checkpoints are registry-controlled and cannot be bypassed by a downstream stage")

    @staticmethod
    def default_definitions() -> tuple[MandatoryCheckpointDefinition, ...]:
        """Return the minimum mandatory checkpoint set."""
        return (
            MandatoryCheckpointDefinition(checkpoint_id="requirements.completeness_review", workflow_stage="requirements", trigger_condition="requirements document is ready for design use", required_human_role="technical_reviewer", control_type=CheckpointControlType.NO_GO_UNTIL_RESOLVED, required_evidence=("requirements_document",), allowed_actions=("review", "request_clarification", "resolve"), block_conditions=("missing_mandatory_input", "unresolved_contradiction", "unbounded_requirement"), release_targets=("design",)),
            MandatoryCheckpointDefinition(checkpoint_id="scope.unsupported_review", workflow_stage="scope_control", trigger_condition="scope matrix is evaluated before design or generation", required_human_role="scope_reviewer", control_type=CheckpointControlType.NO_GO_UNTIL_RESOLVED, required_evidence=("scope_assessment",), allowed_actions=("review", "accept_preview_only", "resolve"), block_conditions=("unsupported_vendor", "unsupported_protocol", "unsupported_scale", "unsupported_regulatory_context"), release_targets=("design", "config_generation", "deployment")),
            MandatoryCheckpointDefinition(checkpoint_id="evidence.sufficiency_review", workflow_stage="evidence_governance", trigger_condition="engineering claim or capability decision is used", required_human_role="technical_reviewer", control_type=CheckpointControlType.NO_GO_UNTIL_RESOLVED, required_evidence=("evidence_chain",), allowed_actions=("review", "request_evidence", "resolve"), block_conditions=("missing_evidence", "stale_evidence", "conflicting_evidence", "unpublished_claim"), release_targets=("design", "equipment", "config_generation", "deployment")),
            MandatoryCheckpointDefinition(checkpoint_id="design.final_review", workflow_stage="design", trigger_condition="final design state is proposed", required_human_role="design_authority", control_type=CheckpointControlType.APPROVAL_REQUIRED, required_evidence=("design_decisions", "verification_report"), allowed_actions=("approve", "approve_with_conditions", "reject", "request_revision"), block_conditions=("failed_verification", "pending_field_feasibility", "unresolved_override"), release_targets=("equipment", "config_generation")),
            MandatoryCheckpointDefinition(checkpoint_id="equipment.bom_review", workflow_stage="equipment", trigger_condition="equipment selection and BOM are complete", required_human_role="technical_reviewer", control_type=CheckpointControlType.REVIEW_ONLY, required_evidence=("capability_evidence", "bom"), allowed_actions=("review", "request_alternative", "accept"), block_conditions=("unsupported_model", "missing_license_scope", "missing_capability_evidence"), release_targets=("config_generation",)),
            MandatoryCheckpointDefinition(checkpoint_id="config.pre_generation_review", workflow_stage="config_generation", trigger_condition="risky configuration generation is requested", required_human_role="technical_reviewer", control_type=CheckpointControlType.APPROVAL_REQUIRED, required_evidence=("design_traceability", "feature_capability_evidence"), allowed_actions=("approve_preview", "request_revision", "reject"), block_conditions=("unsupported_feature", "secret_value_detected", "missing_design_traceability"), release_targets=("deployment_preparation",)),
            MandatoryCheckpointDefinition(checkpoint_id="deployment.pre_go_no_go", workflow_stage="deployment", trigger_condition="production deployment is requested", required_human_role="deployment_approver", control_type=CheckpointControlType.NO_GO_UNTIL_RESOLVED, required_evidence=("backup", "rollback_plan", "verification_report", "change_approval"), allowed_actions=("go", "no_go", "approve_with_conditions"), block_conditions=("active_blocker", "missing_approval", "failed_readiness", "sod_conflict"), release_targets=("deployment_execution",)),
            MandatoryCheckpointDefinition(checkpoint_id="deployment.post_acceptance", workflow_stage="post_deployment", trigger_condition="deployment completes and verification evidence is available", required_human_role="service_owner", control_type=CheckpointControlType.APPROVAL_REQUIRED, required_evidence=("post_deploy_verification", "operational_sot_update"), allowed_actions=("accept", "reject", "open_incident", "request_rollback"), block_conditions=("verification_failed", "unexplained_drift", "missing_operational_evidence"), release_targets=("operations", "handover")),
        )

    def register(self, definition: MandatoryCheckpointDefinition) -> MandatoryCheckpointDefinition:
        """Register an explicit checkpoint definition."""
        self._definitions[definition.checkpoint_id] = definition
        self.record_decision(f"checkpoint:{definition.checkpoint_id}", definition.control_type.value, "mandatory checkpoint definition was registered explicitly")
        return definition

    def get(self, checkpoint_id: str) -> MandatoryCheckpointDefinition:
        """Return one checkpoint definition."""
        return self._definitions[checkpoint_id]

    def all(self) -> tuple[MandatoryCheckpointDefinition, ...]:
        """Return checkpoint definitions in stable order."""
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def for_stage(self, workflow_stage: str) -> tuple[MandatoryCheckpointDefinition, ...]:
        """Return checkpoint definitions for one stage."""
        return tuple(item for item in self._definitions.values() if item.workflow_stage == workflow_stage)
