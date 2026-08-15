from datetime import datetime, timezone, timedelta
from incident_response.incident_metrics import IncidentMetricsCalculator
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity

def test_incident_metrics_calculates_mtta_and_volume():
    detected = datetime.now(timezone.utc)-timedelta(hours=1)
    incident = Incident(incident_id="INC-20260814-0001", title="Issue", description="Issue", severity=IncidentSeverity.P2_HIGH, priority=IncidentPriority.HIGH, category=IncidentCategory.NETWORK_OUTAGE, detected_at=detected, detected_by="operator", detection_method=DetectionMethod.ENGINEER, acknowledged_at=detected+timedelta(minutes=5))
    result = IncidentMetricsCalculator().calculate([incident])
    assert result.total_incidents == 1
    assert result.mtta is not None
