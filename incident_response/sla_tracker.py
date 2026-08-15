"""Incident response and resolution SLA tracking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import Incident, IncidentSeverity, IncidentStatus, SLAProfile, SLAStatus, SLATracking


class SLATracker:
    """Track incident SLAs from explicit timestamps and policy profiles."""

    DEFAULTS = {
        IncidentSeverity.P1_CRITICAL: (15, 30, 240, 0),
        IncidentSeverity.P2_HIGH: (30, 60, 480, 60),
        IncidentSeverity.P3_MEDIUM: (120, 240, 1440, 240),
        IncidentSeverity.P4_LOW: (480, 1440, 2880, 1440),
    }

    def __init__(self, definitions: Mapping[str, Mapping[str, int]] | None = None) -> None:
        """Initialize SLA definitions, defaulting to explicit V1 policy values."""
        self.definitions = dict(definitions or {})
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def profile(self, severity: IncidentSeverity) -> SLAProfile:
        """Return the SLA profile for one severity."""
        values = self.definitions.get(severity.value, {})
        defaults = self.DEFAULTS[severity]
        if not values:
            self.assumptions.append(make_assumption(f"sla:{severity.value}", "v1_default", "external SLA definition was not supplied; V1 default is used and remains reviewable", True))
        return SLAProfile(severity=severity, response_sla=timedelta(minutes=int(values.get("response_minutes", defaults[0]))), update_sla=timedelta(minutes=int(values.get("update_minutes", defaults[1]))), resolution_sla=timedelta(minutes=int(values.get("resolution_minutes", defaults[2]))), escalation_after=timedelta(minutes=int(values.get("escalation_after_minutes", defaults[3]))))

    def evaluate(self, incident: Incident, *, now: datetime | None = None, acknowledged_at: datetime | None = None, resolved_at: datetime | None = None, last_update_at: datetime | None = None) -> SLATracking:
        """Evaluate current SLA status using explicit timestamps."""
        current = now or datetime.now(timezone.utc)
        profile = self.profile(incident.severity)
        response_time = (acknowledged_at or current) - incident.detected_at if acknowledged_at or incident.status != IncidentStatus.NEW else None
        if acknowledged_at is None and incident.status == IncidentStatus.NEW:
            response_status = SLAStatus.ONGOING
        elif response_time is not None and response_time <= profile.response_sla:
            response_status = SLAStatus.MET
        else:
            response_status = SLAStatus.BREACHED
        resolution_time = (resolved_at or current) - incident.detected_at if resolved_at or incident.status in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED} else None
        if resolved_at is not None and resolution_time <= profile.resolution_sla:
            resolution_status = SLAStatus.MET
        elif resolution_time is not None and resolution_time >= profile.resolution_sla:
            resolution_status = SLAStatus.BREACHED
        else:
            resolution_status = SLAStatus.ONGOING
        elapsed = max(timedelta(0), current - incident.detected_at)
        warning_thresholds = [threshold for threshold in (50, 75, 100) if elapsed >= profile.resolution_sla * (threshold / 100)]
        breach_required = 100 in warning_thresholds
        update_due = (last_update_at or incident.detected_at) + profile.update_sla
        decision = make_decision("SLATracker", f"{incident.incident_id}:sla", {"response": response_status.value, "resolution": resolution_status.value}, "compare explicit timestamps with the severity SLA profile", ["SLA_evaluation", "SLA_assumption"], {"SLA_evaluation": "selected", "SLA_assumption": "not selected when timestamps exist"})
        self.decisions.append(decision)
        return SLATracking(incident_id=incident.incident_id, profile=profile, response_time=response_time, response_status=response_status, resolution_time=resolution_time, resolution_status=resolution_status, update_due_at=update_due, warning_thresholds_reached=warning_thresholds, breach_notifications_required=breach_required, assumptions=[item.key for item in self.assumptions])
