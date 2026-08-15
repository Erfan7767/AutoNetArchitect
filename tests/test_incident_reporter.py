from datetime import datetime, timezone
from incident_response.incident_reporter import IncidentReporter
from incident_response.incident_metrics import IncidentMetricsCalculator
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity

def test_incident_reporter_produces_sanitized_reports():
    incident = Incident(incident_id="INC-20260814-0001", title="Issue", description="Issue", severity=IncidentSeverity.P3_MEDIUM, priority=IncidentPriority.MEDIUM, category=IncidentCategory.NETWORK_DEGRADATION, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)
    metrics = IncidentMetricsCalculator().calculate([incident])
    report = IncidentReporter().individual(incident)
    summary = IncidentReporter().summary([incident], metrics, period="weekly")
    assert report["report_metadata"]["automatic_containment_executed"] is False
    assert summary["incident_ids"] == [incident.incident_id]
