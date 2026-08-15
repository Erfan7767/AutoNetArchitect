from incident_response import IncidentManager
from incident_response.incident_models import DetectionMethod, IncidentCategory, IncidentPriority, IncidentSeverity, IncidentStatus


def test_incident_manager_crud_and_lifecycle():
    manager = IncidentManager()
    incident = manager.create(title="Outage", description="Core down", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_by="alice", detection_method=DetectionMethod.ENGINEER)
    assert incident.incident_id.startswith("INC-")
    manager.transition(incident.incident_id, actor="alice", status=IncidentStatus.ACKNOWLEDGED, description="ack")
    manager.transition(incident.incident_id, actor="alice", status=IncidentStatus.INVESTIGATING, description="investigate")
    updated = manager.update(incident.incident_id, actor="alice", changes={"root_cause":"hardware"})
    assert updated.root_cause == "hardware"


def test_incident_manager_rejects_invalid_transition():
    manager = IncidentManager()
    incident = manager.create(title="Issue", description="Issue", severity=IncidentSeverity.P4_LOW, priority=IncidentPriority.LOW, category=IncidentCategory.NETWORK_DEGRADATION, detected_by="alice", detection_method=DetectionMethod.USER)
    try:
        manager.transition(incident.incident_id, actor="alice", status=IncidentStatus.RESOLVED, description="skip")
    except ValueError as error:
        assert "invalid incident transition" in str(error)
    else:
        raise AssertionError("lifecycle jump must be rejected")
