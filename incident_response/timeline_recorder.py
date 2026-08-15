"""Immutable incident timeline recording."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord

from ._common import make_decision, safe_details
from .incident_models import TimelineEntry


class TimelineRecorder:
    """Append immutable timeline entries and never delete or mutate them."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize a local timeline repository."""
        self.audit_trail = audit_trail
        self._entries: dict[str, list[TimelineEntry]] = {}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def record(self, incident_id: str, *, event_type: str, description: str, performed_by: str, evidence: Sequence[str] = (), automated: bool = False, timestamp: datetime | None = None) -> TimelineEntry:
        """Append one immutable entry."""
        if not incident_id or not event_type or not description or not performed_by:
            raise ValueError("incident_id, event_type, description, and performed_by are required")
        if automated and performed_by.lower() in {"unknown", "system"}:
            self.assumptions.append(Assumption(f"{incident_id}:automated_actor", performed_by, "automated events require a traceable system actor; human action is not inferred", True))
        entry = TimelineEntry(timestamp=timestamp or datetime.now(timezone.utc), event_type=event_type, description=description, performed_by=performed_by, evidence=list(dict.fromkeys(str(item) for item in evidence)), automated=automated)
        self._entries.setdefault(incident_id, []).append(entry)
        decision = make_decision("TimelineRecorder", f"{incident_id}:timeline:{len(self._entries[incident_id])}", "append_immutable_entry", "incident timeline entries are append-only for auditability", ["append_immutable_entry", "edit_or_delete_entry"], {"append_immutable_entry": "selected", "edit_or_delete_entry": "rejected"})
        self.decisions.append(decision)
        if self.audit_trail is not None:
            self.audit_trail.record("incident.timeline", performed_by, {"incident_id": incident_id, "event_type": event_type, "evidence": list(evidence), "automated": automated}, outcome="success", correlation_id=incident_id)
        return entry

    def list(self, incident_id: str) -> tuple[TimelineEntry, ...]:
        """Return timeline entries in append order."""
        return tuple(self._entries.get(incident_id, ()))
