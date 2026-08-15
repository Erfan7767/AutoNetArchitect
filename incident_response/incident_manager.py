"""In-memory V1 incident repository with governed lifecycle updates."""

from __future__ import annotations

from datetime import datetime, timezone
import threading
from typing import Any, Mapping

from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord

from ._common import assumption_dict, decision_dict, make_assumption, make_decision, safe_details
from .incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity, IncidentStatus


class IncidentManager:
    """Create, retrieve, update, and close incidents without silent state jumps."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize the local incident repository."""
        self.audit_trail = audit_trail
        self._incidents: dict[str, Incident] = {}
        self._sequence_by_date: dict[str, int] = {}
        self._lock = threading.RLock()
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def create(self, *, title: str, description: str, severity: IncidentSeverity, priority: IncidentPriority, category: IncidentCategory, detected_by: str, detection_method: DetectionMethod, affected_services: list[str] | None = None, affected_devices: list[str] | None = None, affected_sites: list[str] | None = None, affected_users_estimate: int | None = None, assigned_to: str = "", detected_at: datetime | None = None) -> Incident:
        """Create a new incident with an auditable identifier."""
        if not title or not description or not detected_by:
            raise ValueError("title, description, and detected_by are required")
        if affected_users_estimate is not None and affected_users_estimate < 0:
            raise ValueError("affected_users_estimate cannot be negative")
        timestamp = detected_at or datetime.now(timezone.utc)
        date_key = timestamp.strftime("%Y%m%d")
        with self._lock:
            sequence = self._sequence_by_date.get(date_key, 0) + 1
            self._sequence_by_date[date_key] = sequence
            incident_id = f"INC-{date_key}-{sequence:04d}"
            incident = Incident(incident_id=incident_id, title=title, description=description, severity=severity, priority=priority, category=category, detected_at=timestamp, detected_by=detected_by, detection_method=detection_method, affected_services=list(affected_services or []), affected_devices=list(affected_devices or []), affected_sites=list(affected_sites or []), affected_users_estimate=affected_users_estimate, assigned_to=assigned_to)
            decision = make_decision("IncidentManager", f"{incident_id}:creation", "create_incident", "create a local incident record from explicit detection input", ["create_incident", "discard_detection"], {"create_incident": "required for traceability", "discard_detection": "not selected because a detection signal was supplied"})
            incident.decision_records.append(decision_dict(decision))
            incident.assumptions.append(assumption_dict(make_assumption(f"{incident_id}:initial_scope", "supplied_scope_only", "affected services, devices, sites, and user count are not inferred from title text", True)))
            self._incidents[incident_id] = incident
            self.decisions.append(decision)
            self.assumptions.append(make_assumption(f"{incident_id}:initial_scope", "supplied_scope_only", "incident scope is not inferred from a short description", True))
            self._audit("incident.created", detected_by, incident, "success")
            return incident.model_copy(deep=True)

    def get(self, incident_id: str) -> Incident:
        """Return a deep copy of an incident."""
        with self._lock:
            if incident_id not in self._incidents:
                raise KeyError(f"unknown incident: {incident_id}")
            return self._incidents[incident_id].model_copy(deep=True)

    def list(self, *, status: IncidentStatus | None = None, severity: IncidentSeverity | None = None, category: IncidentCategory | None = None) -> tuple[Incident, ...]:
        """List incidents with optional filters."""
        with self._lock:
            values = [item for item in self._incidents.values() if (status is None or item.status == status) and (severity is None or item.severity == severity) and (category is None or item.category == category)]
            return tuple(item.model_copy(deep=True) for item in values)

    def update(self, incident_id: str, *, actor: str, changes: Mapping[str, Any]) -> Incident:
        """Apply an allowed field update without bypassing lifecycle governance."""
        if not actor:
            raise ValueError("actor is required")
        allowed = {"title", "description", "assigned_to", "related_changes", "related_incidents", "diagnostic_session_id", "root_cause", "resolution", "workaround", "affected_services", "affected_devices", "affected_sites", "affected_users_estimate", "impact_assessment", "containment_plan", "eradication_plan", "recovery_plan", "lessons_learned", "decision_records", "assumptions", "escalation_level"}
        forbidden = set(changes) - allowed
        if forbidden:
            raise ValueError(f"unsupported incident update fields: {sorted(forbidden)}")
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                raise KeyError(f"unknown incident: {incident_id}")
            updated = incident.model_copy(update=dict(changes), deep=True)
            updated.decision_records = list(updated.decision_records)
            decision = make_decision("IncidentManager", f"{incident_id}:update:{len(updated.decision_records)}", "update_explicit_fields", "only explicitly supplied incident fields are changed", ["update_explicit_fields", "infer_missing_fields"], {"update_explicit_fields": "selected", "infer_missing_fields": "rejected"})
            updated.decision_records.append(decision_dict(decision))
            self._incidents[incident_id] = updated
            self.decisions.append(decision)
            self._audit("incident.updated", actor, updated, "success")
            return updated.model_copy(deep=True)

    def transition(self, incident_id: str, *, actor: str, status: IncidentStatus, description: str, evidence: list[str] | None = None) -> Incident:
        """Transition only to a lifecycle state allowed by the state machine."""
        if not actor or not description:
            raise ValueError("actor and description are required")
        allowed: dict[IncidentStatus, set[IncidentStatus]] = {
            IncidentStatus.NEW: {IncidentStatus.ACKNOWLEDGED, IncidentStatus.CANCELLED},
            IncidentStatus.ACKNOWLEDGED: {IncidentStatus.INVESTIGATING, IncidentStatus.CANCELLED},
            IncidentStatus.INVESTIGATING: {IncidentStatus.CONTAINMENT, IncidentStatus.ERADICATING, IncidentStatus.CANCELLED},
            IncidentStatus.CONTAINMENT: {IncidentStatus.CONTAINED, IncidentStatus.ERADICATING},
            IncidentStatus.CONTAINED: {IncidentStatus.ERADICATING, IncidentStatus.RECOVERING},
            IncidentStatus.ERADICATING: {IncidentStatus.RECOVERING, IncidentStatus.CONTAINED},
            IncidentStatus.RECOVERING: {IncidentStatus.MONITORING, IncidentStatus.ERADICATING},
            IncidentStatus.MONITORING: {IncidentStatus.RESOLVED, IncidentStatus.RECOVERING},
            IncidentStatus.RESOLVED: {IncidentStatus.CLOSED, IncidentStatus.MONITORING},
            IncidentStatus.CLOSED: set(),
            IncidentStatus.CANCELLED: set(),
        }
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                raise KeyError(f"unknown incident: {incident_id}")
            if status not in allowed[incident.status]:
                raise ValueError(f"invalid incident transition {incident.status.value}->{status.value}")
            now = datetime.now(timezone.utc)
            updated = incident.model_copy(deep=True)
            updated.status = status
            if status == IncidentStatus.ACKNOWLEDGED:
                updated.acknowledged_at = now
            if status == IncidentStatus.CONTAINED:
                updated.contained_at = now
            if status == IncidentStatus.RESOLVED:
                updated.resolved_at = now
                updated.mttr = now - updated.detected_at
            if status == IncidentStatus.CLOSED:
                updated.closed_at = now
                if updated.resolved_at is not None:
                    updated.mttr = updated.resolved_at - updated.detected_at
            from .incident_models import TimelineEntry
            updated.timeline = list(updated.timeline) + [TimelineEntry(event_type=f"status:{status.value}", description=description, performed_by=actor, evidence=list(evidence or []), automated=False)]
            decision = make_decision("IncidentManager", f"{incident_id}:transition:{status.value}", status.value, "follow the explicit incident state machine; do not skip lifecycle gates", [item.value for item in IncidentStatus], {item.value: "not allowed from current state" for item in IncidentStatus if item != status})
            updated.decision_records = list(updated.decision_records) + [decision_dict(decision)]
            self._incidents[incident_id] = updated
            self.decisions.append(decision)
            self._audit("incident.status_transition", actor, updated, "success")
            return updated.model_copy(deep=True)

    def _audit(self, event_type: str, actor: str, incident: Incident, outcome: str) -> None:
        """Write secret-safe incident metadata when an audit trail is configured."""
        if self.audit_trail is None:
            return
        self.audit_trail.record(event_type, actor, {"incident_id": incident.incident_id, "status": incident.status.value, "severity": incident.severity.value, "category": incident.category.value, "affected_services": incident.affected_services, "affected_devices": incident.affected_devices, "affected_sites": incident.affected_sites, "evidence_count": len(incident.timeline), "write_execution": False}, outcome=outcome, correlation_id=incident.incident_id)
