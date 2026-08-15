"""Review-session contracts for the engineer console."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from audit.audit_trail import AuditTrail
from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class ReviewSessionStatus(str, Enum):
    """Lifecycle state of an engineer review session."""

    OPEN = "open"
    PAUSED = "paused"
    SUBMITTED = "submitted"
    CLOSED = "closed"


class ReviewSessionEvent(BaseModel):
    """Audit-friendly event in a review session."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    session_id: str
    actor_id: str
    actor_role: str
    action: str
    note: str = ""
    reference: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewSession(BaseModel):
    """State carried by the presentation layer without owning decision logic."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    workflow: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    reviewer_role: str = Field(min_length=1)
    status: ReviewSessionStatus = ReviewSessionStatus.OPEN
    decision_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_references: dict[str, str] = Field(default_factory=dict)


class ReviewSessionManager(BaseDesigner):
    """Manage console session state and delegate decisions to existing services."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize session manager with optional audit integration."""
        super().__init__("ReviewSessionManager")
        self.audit_trail = audit_trail
        self._sessions: dict[str, ReviewSession] = {}
        self._events: dict[str, ReviewSessionEvent] = {}
        self.record_decision("console_policy", "presentation_only", "review console stores session context and delegates approvals, overrides, and decisions to existing services")

    def start(self, session: ReviewSession) -> ReviewSession:
        """Open a new review session without altering business artifacts."""
        if session.session_id in self._sessions:
            raise ValueError(f"review session already exists: {session.session_id}")
        self._sessions[session.session_id] = session
        self._audit(session, "session_started", "")
        return session

    def record_event(self, session_id: str, *, actor_id: str, actor_role: str, action: str, note: str = "", reference: str = "") -> ReviewSessionEvent:
        """Record a human console action as metadata only."""
        session = self._sessions[session_id]
        event = ReviewSessionEvent(event_id=f"{session_id}:{len(self._events) + 1}", session_id=session_id, actor_id=actor_id, actor_role=actor_role, action=action, note=note, reference=reference)
        self._events[event.event_id] = event
        updated = session.model_copy(update={"event_ids": session.event_ids + (event.event_id,), "notes": session.notes + ((note,) if note else ()), "updated_at": datetime.now(timezone.utc)})
        self._sessions[session_id] = updated
        self.record_decision(f"session_event:{event.event_id}", action, "console event retained without reimplementing business approval logic")
        self._audit(updated, action, reference)
        return event

    def update_status(self, session_id: str, status: ReviewSessionStatus, *, actor_id: str, actor_role: str, note: str = "") -> ReviewSession:
        """Change session presentation state and record the action."""
        session = self._sessions[session_id]
        updated = session.model_copy(update={"status": status, "updated_at": datetime.now(timezone.utc), "notes": session.notes + ((note,) if note else ())})
        self._sessions[session_id] = updated
        self.record_event(session_id, actor_id=actor_id, actor_role=actor_role, action=f"status:{status.value}", note=note)
        return self._sessions[session_id]

    def get(self, session_id: str) -> ReviewSession:
        """Return one review session."""
        return self._sessions[session_id]

    def events(self, session_id: str) -> tuple[ReviewSessionEvent, ...]:
        """Return session events in insertion order."""
        session = self._sessions[session_id]
        return tuple(self._events[event_id] for event_id in session.event_ids)

    def _audit(self, session: ReviewSession, action: str, reference: str) -> None:
        """Record secret-safe console metadata when audit is available."""
        if self.audit_trail is not None:
            self.audit_trail.record("review_console.session", session.reviewer_id, {"session_id": session.session_id, "project_id": session.project_id, "workflow": session.workflow, "status": session.status.value, "action": action, "reference": reference, "decision_ids": list(session.decision_ids)}, outcome="recorded")
