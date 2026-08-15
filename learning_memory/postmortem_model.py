"""Postmortem contracts for failure memory."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PostmortemStatus(str, Enum):
    """Postmortem review state."""

    OPEN = "open"
    REVIEW_REQUIRED = "review_required"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class TimelineEvent(BaseModel):
    """One evidence-linked event in a postmortem timeline."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    timestamp: datetime
    description: str
    source: str
    evidence_ids: tuple[str, ...] = ()


class PostmortemRecord(BaseModel):
    """Human-reviewable postmortem with explicit knowledge consequences."""

    model_config = ConfigDict(extra="forbid")

    postmortem_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    discrepancy_ids: tuple[str, ...] = ()
    failure_ids: tuple[str, ...] = ()
    timeline: tuple[TimelineEvent, ...] = ()
    actual_impact: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)
    contributing_factors: tuple[str, ...] = ()
    corrective_actions: tuple[str, ...] = ()
    prevention_recommendations: tuple[str, ...] = ()
    human_correction: str = ""
    evidence_status: str = "not_available"
    evidence_ids: tuple[str, ...] = ()
    owner_role: str = "engineer_in_charge"
    status: PostmortemStatus = PostmortemStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
