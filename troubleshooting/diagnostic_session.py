"""Lifecycle state for auditable troubleshooting sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field


class SessionEvent(BaseModel):
    """One session timeline event."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class DiagnosticSession:
    """Track diagnostic lifecycle and governance metadata."""

    def __init__(self, diagnostic_id: str, reported_by: str) -> None:
        """Create a new session in created state."""
        if not diagnostic_id or not reported_by:
            raise ValueError("diagnostic_id and reported_by are required")
        self.diagnostic_id = diagnostic_id
        self.reported_by = reported_by
        self.state = "created"
        self.events: list[SessionEvent] = []
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def transition(self, state: str, description: str, evidence_ids: list[str] | None = None) -> SessionEvent:
        """Advance the session to a named state and record a timeline event."""
        allowed = {"created", "classified", "evidence_collection", "workflow_execution", "rca", "remediation_advice", "escalation", "completed", "blocked", "failed"}
        if state not in allowed:
            raise ValueError(f"unsupported diagnostic session state: {state}")
        self.state = state
        event = SessionEvent(event_type=state, description=description, evidence_ids=list(evidence_ids or []))
        self.events.append(event)
        return event

    def record_decision(self, decision: DecisionRecord) -> None:
        """Append a DecisionRecord to the session."""
        self.decisions.append(decision)

    def record_assumption(self, assumption: Assumption) -> None:
        """Append an Assumption to the session."""
        self.assumptions.append(assumption)

    def export(self) -> dict[str, Any]:
        """Export session metadata without raw secret material."""
        return {"diagnostic_id": self.diagnostic_id, "reported_by": self.reported_by, "state": self.state, "events": [event.model_dump(mode="json") for event in self.events], "decisions": [decision.__dict__ for decision in self.decisions], "assumptions": [assumption.__dict__ for assumption in self.assumptions]}
