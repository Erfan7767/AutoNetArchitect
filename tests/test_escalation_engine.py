from incident_response.escalation_engine import EscalationEngine
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity
from datetime import datetime, timezone, timedelta


def _incident(severity):
    return Incident(incident_id="INC-20260814-0001", title="issue", description="issue", severity=severity, priority=IncidentPriority.CRITICAL if severity.value == "P1" else IncidentPriority.HIGH, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)


def test_escalation_engine_escalates_p1_and_requires_war_room():
    result = EscalationEngine().evaluate(_incident(IncidentSeverity.P1_CRITICAL))
    assert result.level == 4
    assert result.war_room_required is True


def test_escalation_engine_uses_time_and_scope():
    result = EscalationEngine().evaluate(_incident(IncidentSeverity.P3_MEDIUM), elapsed=timedelta(hours=5), scope_spreading=True)
    assert result.level >= 2
