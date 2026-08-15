"""Structured lessons learned from discrepancies and failures."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceStatus(str, Enum):
    """Evidence sufficiency attached to a lesson."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    CONFLICTING = "conflicting"
    NOT_AVAILABLE = "not_available"


class LessonStatus(str, Enum):
    """Lifecycle status for a lesson."""

    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    VALIDATED = "validated"
    PUBLISHED = "published"
    RETIRED = "retired"


class LessonRecord(BaseModel):
    """A traceable lesson that never hides evidence weakness."""

    model_config = ConfigDict(extra="forbid")

    lesson_id: str = Field(min_length=1)
    scenario_ids: tuple[str, ...] = ()
    discrepancy_ids: tuple[str, ...] = ()
    failure_ids: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    root_cause: str = Field(min_length=1)
    contributing_factors: tuple[str, ...] = ()
    evidence_status: EvidenceStatus = EvidenceStatus.NOT_AVAILABLE
    evidence_ids: tuple[str, ...] = ()
    corrective_action: str = Field(min_length=1)
    prevention_recommendation: str = Field(min_length=1)
    human_correction_summary: str = ""
    recurrence_count: int = 1
    confidence: float = 0.0
    status: LessonStatus = LessonStatus.DRAFT
    owner_role: str = "engineer_in_charge"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: datetime | None = None

    def model_post_init(self, __context: object) -> None:
        """Validate confidence and recurrence count."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("lesson confidence must be between zero and one")
        if self.recurrence_count < 1:
            raise ValueError("lesson recurrence_count must be at least one")
