from datetime import datetime, timezone, timedelta
from incident_response.incident_correlation import IncidentCorrelationEngine
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity

def _incident(i, title, offset):
    return Incident(incident_id=f"INC-20260814-{i:04d}", title=title, description=title, severity=IncidentSeverity.P2_HIGH, priority=IncidentPriority.HIGH, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc)+timedelta(seconds=offset), detected_by="operator", detection_method=DetectionMethod.ENGINEER, affected_devices=["core-1"])

def test_incident_correlation_detects_duplicates_and_does_not_verify_causality():
    result = IncidentCorrelationEngine().correlate([_incident(1, "same", 0), _incident(2, "same", 60)])
    assert result[0].correlation_type == "duplicate"
    assert result[0].causal_claim_verified is False
