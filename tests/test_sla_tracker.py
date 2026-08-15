from datetime import datetime, timezone, timedelta
from incident_response.sla_tracker import SLATracker
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity, SLAStatus

def test_sla_tracker_detects_met_response_and_ongoing_resolution():
    detected = datetime.now(timezone.utc) - timedelta(minutes=5)
    incident = Incident(incident_id="INC-20260814-0001", title="Issue", description="Issue", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_at=detected, detected_by="operator", detection_method=DetectionMethod.ENGINEER)
    result = SLATracker().evaluate(incident, now=datetime.now(timezone.utc), acknowledged_at=detected + timedelta(minutes=2))
    assert result.response_status == SLAStatus.MET
    assert result.resolution_status == SLAStatus.ONGOING

def test_sla_tracker_keeps_missing_definitions_reviewable():
    tracker = SLATracker()
    profile = tracker.profile(IncidentSeverity.P4_LOW)
    assert profile.response_sla.total_seconds() > 0
    assert tracker.assumptions
