"""Shared contracts for safe deployment execution workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class DeploymentMode(str, Enum):
    """Execution mode."""

    DRY_RUN = "dry_run"
    REAL = "real"


class DeploymentState(str, Enum):
    """Deployment operation and batch states."""

    DRY_RUN = "dry_run"
    EXECUTED = "executed"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLBACK_REVIEW = "rollback_review"
    ROLLED_BACK = "rolled_back"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_APPROVAL = "blocked_approval"
    BLOCKED_BACKUP = "blocked_backup"
    BLOCKED_INVALID_PROJECT_STATE = "blocked_invalid_project_state"
    BLOCKED_HUMAN_DATA = "blocked_human_data"
    BLOCKED_UNSUPPORTED = "blocked_unsupported"


@dataclass(frozen=True)
class DeploymentRequest:
    """Deployment request containing references and execution policy inputs."""

    deployment_id: str
    change_id: str
    device_id: str
    vendor: str
    platform: str
    transport: str
    rendered_config: str = ""
    endpoint_reference: str = ""
    credential_reference: str = ""
    secret_references: tuple[str, ...] = ()
    project_valid: bool = True
    unresolved_human_inputs: tuple[str, ...] = ()
    approved: bool = False
    backup_reference: str = ""
    rollback_reference: str = ""
    verification_required: bool = True
    rollback_required: bool = True
    dry_run: bool = True
    production_requested: bool = False
    remote_destructive: bool = False
    actor: str = ""
    evidence_ids: tuple[str, ...] = ()
    governance_required: bool = False
    governance_workflow: str = "deployment"
    governance_risk_class: str = "critical"
    signoff_references: tuple[str, ...] = ()
    reviewer_references: tuple[str, ...] = ()
    accountable_owner_reference: str = ""
    execution_authority_reference: str = ""
    governance_checkpoints: tuple[dict[str, Any], ...] = ()
    supervised_mode: bool = True
    supervision_checkpoint_id: str = "deployment.execution_gate"
    supervision_reviewer_id: str = ""
    supervision_reviewer_role: str = ""
    supervision_reviewer_action: str = ""
    supervision_reviewer_rationale: str = ""
    supervision_reviewer_reference: str = ""
    supervision_approver_id: str = ""
    supervision_approver_role: str = ""
    supervision_approval_action: str = ""
    supervision_approval_rationale: str = ""
    supervision_approval_reference: str = ""
    override_ids: tuple[str, ...] = ()
    decision_provenance: tuple[str, ...] = ()
    review_control_enabled: bool = False
    review_control_stage: str = "deployment"
    review_control_checkpoint_records: tuple[dict[str, Any], ...] = ()
    review_control_blockers: tuple[dict[str, Any], ...] = ()
    review_control_approval_present: bool = False
    review_control_governance_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize request without resolving any secret reference."""
        return asdict(self) | {"secret_references": list(self.secret_references), "unresolved_human_inputs": list(self.unresolved_human_inputs), "evidence_ids": list(self.evidence_ids), "signoff_references": list(self.signoff_references), "reviewer_references": list(self.reviewer_references), "governance_checkpoints": list(self.governance_checkpoints), "supervised_mode": self.supervised_mode, "supervision_checkpoint_id": self.supervision_checkpoint_id, "override_ids": list(self.override_ids), "decision_provenance": list(self.decision_provenance), "review_control_checkpoint_records": list(self.review_control_checkpoint_records), "review_control_blockers": list(self.review_control_blockers)}


@dataclass(frozen=True)
class DeploymentOperation:
    """Result of one transport-specific operation."""

    operation_id: str
    deployment_id: str
    protocol: str
    device_id: str
    state: str
    dry_run: bool
    backup_created: bool
    config_hash: str
    output: str = ""
    provider_reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    rollback_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize operation result."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "reasons": list(self.reasons)}


@dataclass(frozen=True)
class DeploymentResult:
    """Complete deployment result including gate, verification, and rollback references."""

    deployment_id: str
    state: str
    gate: str
    operation: DeploymentOperation | None
    verification: Any = None
    rollback: Any = None
    required_human_inputs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result without exposing raw secrets."""
        return {"deployment_id": self.deployment_id, "state": self.state, "gate": self.gate, "operation": self.operation.to_dict() if self.operation else None, "verification": self.verification.to_dict() if hasattr(self.verification, "to_dict") else self.verification, "rollback": self.rollback.to_dict() if hasattr(self.rollback, "to_dict") else self.rollback, "required_human_inputs": list(self.required_human_inputs), "reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}
