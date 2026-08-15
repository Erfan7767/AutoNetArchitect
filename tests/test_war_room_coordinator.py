from incident_response.war_room_coordinator import WarRoomCoordinator
from incident_response.incident_models import DetectionMethod, Incident, IncidentCategory, IncidentPriority, IncidentSeverity
from datetime import datetime, timezone

def _p1():
    return Incident(incident_id="INC-20260814-0001", title="Core", description="Core", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)

def test_war_room_requires_human_commander():
    room = WarRoomCoordinator().initiate(_p1(), incident_commander="alice", participants=["bob"])
    assert room.active is True
    assert "alice" in room.participant_list

def test_war_room_rejects_automatic_commander():
    try:
        WarRoomCoordinator().initiate(_p1(), incident_commander="automatic", participants=["bob"])
    except ValueError as error:
        assert "human" in str(error)
    else:
        raise AssertionError("automatic commander must be rejected")
