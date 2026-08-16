"""Responsibility boundaries for an engineer-supervised multi-agent workflow.

The model intentionally assigns review and preparation work only.  It never
grants an agent authority to configure a production device or approve a change.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AgentRole(str, Enum):
    """Specialized responsibilities available to the local coordination layer."""

    AUTHORIZED_DISCOVERY = "authorized_discovery"
    EVIDENCE_REVIEW = "evidence_review"
    DESIGN_PREPARATION = "design_preparation"
    CAPABILITY_ASSESSMENT = "capability_assessment"
    VIRTUAL_VALIDATION = "virtual_validation"
    SAFETY_REVIEW = "safety_review"
    RELEASE_COORDINATION = "release_coordination"


class CoordinationStage(str, Enum):
    """Evidence stages shared by cooperating agents and the human operator."""

    SCOPE_CONFIRMED = "scope_confirmed"
    DISCOVERY = "discovery"
    EVIDENCE_REVIEW = "evidence_review"
    DESIGN_PREPARATION = "design_preparation"
    CAPABILITY_ASSESSMENT = "capability_assessment"
    VIRTUAL_VALIDATION = "virtual_validation"
    SAFETY_REVIEW = "safety_review"
    HUMAN_GO_NO_GO = "human_go_no_go"


class AgentResponsibility(BaseModel):
    """Bounded responsibility and output required from a specialized agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: AgentRole
    stage: CoordinationStage
    permitted_actions: tuple[str, ...] = Field(min_length=1)
    required_inputs: tuple[str, ...] = Field(min_length=1)
    required_outputs: tuple[str, ...] = Field(min_length=1)
    prohibited_actions: tuple[str, ...] = Field(min_length=1)
    requires_named_human_authority: bool = True


class AgentAssignment(BaseModel):
    """Secret-free assignment binding a specialist to one approved site scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str = Field(min_length=1, max_length=160)
    role: AgentRole
    site_id: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=1, max_length=160)
    authority_reference: str = Field(min_length=1, max_length=200)


class MultiAgentResponsibilityModel:
    """Resolve responsibilities and guard stage handoffs for cooperating agents."""

    _RESPONSIBILITIES: dict[AgentRole, AgentResponsibility] = {
        AgentRole.AUTHORIZED_DISCOVERY: AgentResponsibility(
            role=AgentRole.AUTHORIZED_DISCOVERY,
            stage=CoordinationStage.DISCOVERY,
            permitted_actions=("collect_read_only_device_facts", "record_no_guess_outcome"),
            required_inputs=("approved_scope", "target", "protocol", "credential_reference"),
            required_outputs=("secret_free_discovery_result", "evidence_provenance"),
            prohibited_actions=("scan_outside_scope", "modify_device_configuration", "store_secret_value"),
        ),
        AgentRole.EVIDENCE_REVIEW: AgentResponsibility(
            role=AgentRole.EVIDENCE_REVIEW,
            stage=CoordinationStage.EVIDENCE_REVIEW,
            permitted_actions=("classify_observed_evidence", "preserve_ambiguity", "raise_blocker"),
            required_inputs=("discovery_result", "evidence_provenance", "approved_scope"),
            required_outputs=("reviewed_evidence_state", "unresolved_items"),
            prohibited_actions=("infer_missing_device_fact", "replace_ambiguous_result", "approve_release"),
        ),
        AgentRole.DESIGN_PREPARATION: AgentResponsibility(
            role=AgentRole.DESIGN_PREPARATION,
            stage=CoordinationStage.DESIGN_PREPARATION,
            permitted_actions=("prepare_versioned_design_artifact", "record_rationale", "flag_missing_input"),
            required_inputs=("approved_requirements", "reviewed_evidence_state", "sector_constraints"),
            required_outputs=("design_artifact", "decision_rationale", "unresolved_items"),
            prohibited_actions=("invent_device_attribute", "generate_unchecked_command", "approve_release"),
        ),
        AgentRole.CAPABILITY_ASSESSMENT: AgentResponsibility(
            role=AgentRole.CAPABILITY_ASSESSMENT,
            stage=CoordinationStage.CAPABILITY_ASSESSMENT,
            permitted_actions=("evaluate_versioned_capability_evidence", "return_safe_refusal", "raise_blocker"),
            required_inputs=("observed_platform", "software_version", "license_evidence", "design_artifact"),
            required_outputs=("capability_assessment", "unsupported_or_unresolved_items"),
            prohibited_actions=("assume_license", "substitute_vendor_command", "approve_release"),
        ),
        AgentRole.VIRTUAL_VALIDATION: AgentResponsibility(
            role=AgentRole.VIRTUAL_VALIDATION,
            stage=CoordinationStage.VIRTUAL_VALIDATION,
            permitted_actions=("queue_supported_validation", "bind_hashes", "record_test_outcome"),
            required_inputs=("artifact_hash", "target_facts_hash", "scope_hash", "validation_path"),
            required_outputs=("virtual_test_result", "fidelity_label", "evidence_reference"),
            prohibited_actions=("treat_logical_test_as_production_proof", "change_production_device", "approve_release"),
        ),
        AgentRole.SAFETY_REVIEW: AgentResponsibility(
            role=AgentRole.SAFETY_REVIEW,
            stage=CoordinationStage.SAFETY_REVIEW,
            permitted_actions=("evaluate_release_blockers", "verify_control_evidence", "return_no_go"),
            required_inputs=("virtual_test_result", "backup_evidence", "maintenance_evidence", "capability_assessment"),
            required_outputs=("approval_readiness", "blocker_list"),
            prohibited_actions=("waive_required_control", "approve_release", "execute_change"),
        ),
        AgentRole.RELEASE_COORDINATION: AgentResponsibility(
            role=AgentRole.RELEASE_COORDINATION,
            stage=CoordinationStage.HUMAN_GO_NO_GO,
            permitted_actions=("assemble_review_pack", "request_human_decision", "record_approval_reference"),
            required_inputs=("approval_readiness", "blocker_list", "human_authority"),
            required_outputs=("human_go_no_go_request", "immutable_review_reference"),
            prohibited_actions=("self_approve", "execute_change", "override_no_go"),
        ),
    }

    _STAGE_ORDER: tuple[CoordinationStage, ...] = (
        CoordinationStage.SCOPE_CONFIRMED,
        CoordinationStage.DISCOVERY,
        CoordinationStage.EVIDENCE_REVIEW,
        CoordinationStage.DESIGN_PREPARATION,
        CoordinationStage.CAPABILITY_ASSESSMENT,
        CoordinationStage.VIRTUAL_VALIDATION,
        CoordinationStage.SAFETY_REVIEW,
        CoordinationStage.HUMAN_GO_NO_GO,
    )

    def responsibility_for(self, role: AgentRole) -> AgentResponsibility:
        """Return the immutable responsibility definition for one specialist role."""

        return self._RESPONSIBILITIES[role]

    def stage_follows(self, prior: CoordinationStage, candidate: CoordinationStage) -> bool:
        """Return whether a candidate handoff is the immediate valid next stage."""

        prior_index = self._STAGE_ORDER.index(prior)
        return prior_index + 1 < len(self._STAGE_ORDER) and self._STAGE_ORDER[prior_index + 1] is candidate

    def assignment_matches_scope(self, assignment: AgentAssignment, site_id: str, scope_hash: str) -> bool:
        """Check scope binding without inspecting credentials or contacting a device."""

        return assignment.site_id == site_id and assignment.scope_hash == scope_hash

    def production_execution_permitted(self, role: AgentRole) -> bool:
        """Always deny production execution because no specialist role carries that authority."""

        _ = role
        return False

