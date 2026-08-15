"""Review class taxonomy and human review records."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import Assumption, BaseDesigner, DecisionRecord


class ReviewClass(str, Enum):
    """Human review categories used throughout the project lifecycle."""

    INFORMATIONAL = "informational_review"
    TECHNICAL = "technical_review"
    SECURITY = "security_review"
    COMPLIANCE = "compliance_review"
    DEPLOYMENT_APPROVAL = "deployment_approval"
    EMERGENCY = "emergency_review"


class ReviewOutcome(str, Enum):
    """Review decision states."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    ACCEPTED_WITH_CONDITIONS = "accepted_with_conditions"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class ReviewClassDefinition(BaseModel):
    """Policy definition for one review class."""

    model_config = ConfigDict(extra="forbid")

    review_class: ReviewClass
    title_en: str
    title_ar: str
    required_role: str
    purpose: str
    blocks_execution: bool = True
    minimum_risk: str = "low"


class ReviewRecord(BaseModel):
    """Immutable-style record of one human review checkpoint."""

    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    decision_class: str = Field(min_length=1)
    risk_class: str = Field(min_length=1)
    review_class: ReviewClass
    reviewer_id: str = Field(min_length=1)
    reviewer_role: str = Field(min_length=1)
    outcome: ReviewOutcome = ReviewOutcome.PENDING
    rationale: str = ""
    conditions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    decided_at: datetime | None = None
    expires_at: datetime | None = None

    def is_accepted(self, now: datetime | None = None) -> bool:
        """Return whether the review is accepted and not expired."""
        selected_now = now or datetime.now(timezone.utc)
        if self.outcome not in {ReviewOutcome.ACCEPTED, ReviewOutcome.ACCEPTED_WITH_CONDITIONS}:
            return False
        if self.expires_at is None:
            return True
        expiry = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return expiry > selected_now


class ReviewClassRegistry(BaseDesigner):
    """Registry of review classes and their required human roles."""

    def __init__(self, definitions: list[ReviewClassDefinition] | None = None) -> None:
        """Load the conservative default taxonomy and optional overrides."""
        super().__init__("ReviewClassRegistry")
        self._definitions: dict[ReviewClass, ReviewClassDefinition] = {item.review_class: item for item in self.default_definitions()}
        for item in definitions or []:
            self._definitions[item.review_class] = item
        self.record_decision("review_taxonomy", sorted(item.value for item in self._definitions), "review categories are explicit and cannot be inferred from execution success")

    @staticmethod
    def default_definitions() -> tuple[ReviewClassDefinition, ...]:
        """Return default review class definitions."""
        return (
            ReviewClassDefinition(review_class=ReviewClass.INFORMATIONAL, title_en="Informational Review", title_ar="مراجعة معلوماتية", required_role="informational_reviewer", purpose="Acknowledge context without authorizing execution.", blocks_execution=False, minimum_risk="low"),
            ReviewClassDefinition(review_class=ReviewClass.TECHNICAL, title_en="Technical Review", title_ar="مراجعة تقنية", required_role="technical_reviewer", purpose="Validate design or engineering rationale.", blocks_execution=True, minimum_risk="medium"),
            ReviewClassDefinition(review_class=ReviewClass.SECURITY, title_en="Security Review", title_ar="مراجعة أمنية", required_role="security_reviewer", purpose="Validate security-impacting controls and risks.", blocks_execution=True, minimum_risk="high"),
            ReviewClassDefinition(review_class=ReviewClass.COMPLIANCE, title_en="Compliance Review", title_ar="مراجعة امتثال", required_role="compliance_reviewer", purpose="Review technical control scope and evidence boundaries.", blocks_execution=True, minimum_risk="high"),
            ReviewClassDefinition(review_class=ReviewClass.DEPLOYMENT_APPROVAL, title_en="Deployment Approval", title_ar="اعتماد النشر", required_role="deployment_approver", purpose="Authorize a governed deployment path.", blocks_execution=True, minimum_risk="high"),
            ReviewClassDefinition(review_class=ReviewClass.EMERGENCY, title_en="Emergency Review", title_ar="مراجعة طارئة", required_role="on_call_manager", purpose="Authorize a narrowly scoped emergency change with retrospective review.", blocks_execution=True, minimum_risk="critical"),
        )

    def definition(self, review_class: ReviewClass | str) -> ReviewClassDefinition:
        """Return a review class definition."""
        return self._definitions[ReviewClass(review_class)]

    def role_for(self, review_class: ReviewClass | str) -> str:
        """Return the required role for a review class."""
        return self.definition(review_class).required_role

    def definitions(self) -> tuple[ReviewClassDefinition, ...]:
        """Return definitions in stable order."""
        return tuple(self._definitions[key] for key in sorted(self._definitions, key=lambda item: item.value))

    def record_review(self, record: ReviewRecord) -> ReviewRecord:
        """Record a review decision with explicit rationale and decision metadata."""
        if record.outcome in {ReviewOutcome.ACCEPTED, ReviewOutcome.ACCEPTED_WITH_CONDITIONS, ReviewOutcome.REJECTED} and not record.rationale.strip():
            raise ValueError("a decided review requires rationale")
        decided = record
        if record.decided_at is None and record.outcome != ReviewOutcome.PENDING:
            decided = record.model_copy(update={"decided_at": datetime.now(timezone.utc)})
        self.record_decision(f"review:{decided.review_id}", decided.outcome.value, "human review outcome was recorded with explicit reviewer identity and rationale")
        return decided
