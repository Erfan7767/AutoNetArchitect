from incident_response.communication_manager import CommunicationManager
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity
from datetime import datetime, timezone

def test_communication_manager_generates_bilingual_unsent_artifacts():
    incident = Incident(incident_id="INC-20260814-0001", title="Outage", description="Core issue", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)
    manager = CommunicationManager()
    en = manager.generate(incident, communication_type="initial_notification", audience="management", channel="email", language="en")
    ar = manager.generate(incident, communication_type="status_update", audience="affected_users", channel="chat", language="ar")
    assert en.sent is False
    assert ar.language == "ar"
    assert ar.body
