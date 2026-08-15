"""Human checkpoint and sign-off policy enforcement."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .accountability_matrix import AccountabilityRequirement
from .review_classes import ReviewOutcome


class CheckpointType(str, Enum):
    """Distinct human accountability dimensions."""

    REVIEW = "review"
    APPROVAL = "approval"
    ACCOUNTABILITY = "accountability"
    EXECUTION_AUTHORITY = "execution_authority"


class CheckpointRecord(BaseModel):
    """One human checkpoint record."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    checkpoint_type: CheckpointType
    principal_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    outcome: ReviewOutcome = ReviewOutcome.PENDING
    rationale: str = ""
    reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    def is_current(self, now: datetime | None = None) -> bool:
        """Return whether the checkpoint is accepted and not expired."""
        selected_now = now or datetime.now(timezone.utc)
        if self.outcome not in {ReviewOutcome.ACCEPTED, ReviewOutcome.ACCEPTED_WITH_CONDITIONS}:
            return False
        if self.expires_at is None:
            return True
        expiry = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return expiry > selected_now


class SignoffEvaluation(BaseModel):
    """Explainable result of sign-off evaluation."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    allowed: bool
    state: str
    required_reviews: tuple[str, ...] = ()
    completed_reviews: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    completed_approvals: tuple[str, ...] = ()
    required_accountability: str | None = None
    completed_accountability: str | None = None
    required_execution_authority: tuple[str, ...] = ()
    completed_execution_authority: tuple[str, ...] = ()
    pending_checkpoints: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    decision_reference: str = ""


class SignoffPolicy(BaseDesigner):
    """Enforce explicit human sign-off for policy-controlled workflows."""

    def __init__(self) -> None:
        """Initialize the sign-off evaluator."""
        super().__init__("SignoffPolicy")
        self.record_decision("signoff_enforcement", "deny_by_default", "required human checkpoints must be current, role-matched, and separately modeled")

    def evaluate(self, requirement: AccountabilityRequirement, checkpoints: Iterable[CheckpointRecord], *, now: datetime | None = None) -> SignoffEvaluation:
        """Evaluate all required checkpoint dimensions."""
        selected_now = now or datetime.now(timezone.utc)
        current = [item for item in checkpoints if item.workflow == requirement.workflow and item.is_current(selected_now)]
        reviews = {item.role for item in current if item.checkpoint_type == CheckpointType.REVIEW}
        approvals = {item.role for item in current if item.checkpoint_type == CheckpointType.APPROVAL}
        accountability = next((item.role for item in current if item.checkpoint_type == CheckpointType.ACCOUNTABILITY and item.role == requirement.accountable_owner_role), None)
        execution_roles = {item.role for item in current if item.checkpoint_type == CheckpointType.EXECUTION_AUTHORITY}
        required_reviews = tuple(role for role in requirement.required_reviewer_roles)
        required_approvals = tuple(role for role in requirement.required_approver_roles)
        required_execution = tuple(role for role in requirement.execution_authority_roles)
        completed_reviews = tuple(role for role in required_reviews if role in reviews)
        completed_approvals = tuple(role for role in required_approvals if role in approvals)
        completed_execution = tuple(role for role in required_execution if role in execution_roles)
        pending: list[str] = []
        reasons: list[str] = []
        if requirement.review_required:
            pending.extend(f"review:{role}" for role in required_reviews if role not in reviews)
        if requirement.approval_required:
            pending.extend(f"approval:{role}" for role in required_approvals if role not in approvals)
        if requirement.accountable_owner_role and accountability is None:
            pending.append(f"accountability:{requirement.accountable_owner_role}")
        if requirement.execution_authority_required:
            pending.extend(f"execution_authority:{role}" for role in required_execution if role not in execution_roles)
        if pending:
            reasons.append("one or more required human checkpoints are missing, pending, rejected, or expired")
        allowed = not pending
        state = "approved" if allowed else "blocked_pending_signoff"
        self.record_decision(f"signoff:{requirement.workflow}", state, "sign-off evaluation distinguishes review, approval, accountability, and execution authority")
        evidence = tuple(dict.fromkeys(item for record in current for item in record.evidence_ids))
        return SignoffEvaluation(workflow=requirement.workflow, allowed=allowed, state=state, required_reviews=required_reviews, completed_reviews=completed_reviews, required_approvals=required_approvals, completed_approvals=completed_approvals, required_accountability=requirement.accountable_owner_role, completed_accountability=accountability, required_execution_authority=required_execution, completed_execution_authority=completed_execution, pending_checkpoints=tuple(pending), reasons=tuple(reasons), evidence_ids=evidence, decision_reference=f"governance://signoff/{requirement.workflow}")

    def record_checkpoint(self, checkpoint: CheckpointRecord) -> CheckpointRecord:
        """Validate and record one checkpoint without treating it as another checkpoint type."""
        if checkpoint.outcome in {ReviewOutcome.ACCEPTED, ReviewOutcome.ACCEPTED_WITH_CONDITIONS, ReviewOutcome.REJECTED} and not checkpoint.rationale.strip():
            raise ValueError("decided checkpoint requires rationale")
        if checkpoint.checkpoint_type in {CheckpointType.APPROVAL, CheckpointType.EXECUTION_AUTHORITY} and checkpoint.outcome in {ReviewOutcome.ACCEPTED, ReviewOutcome.ACCEPTED_WITH_CONDITIONS} and not checkpoint.reference.startswith("approval://"):
            raise ValueError("approval and execution authority checkpoints require an approval:// reference")
        self.record_decision(f"checkpoint:{checkpoint.checkpoint_id}", checkpoint.outcome.value, "human checkpoint recorded with explicit type, role, reference, and rationale")
        return checkpoint
