from datetime import datetime, timezone
from incident_response.incident_models import Incident, IncidentCategory, IncidentPriority, IncidentSeverity, DetectionMethod, IncidentPlanStep


def test_incident_contract_and_id_pattern():
    incident = Incident(incident_id="INC-20260814-0001", title="Core outage", description="Core unavailable", severity=IncidentSeverity.P1_CRITICAL, priority=IncidentPriority.CRITICAL, category=IncidentCategory.NETWORK_OUTAGE, detected_at=datetime.now(timezone.utc), detected_by="operator", detection_method=DetectionMethod.ENGINEER)
    assert incident.incident_id.startswith("INC-")
    assert incident.status.value == "new"


def test_incident_plan_requires_approval():
    try:
        IncidentPlanStep(step_id="s1", action="unsafe", risk="high", requires_approval=False, verification="verify")
    except ValueError as error:
        assert "approval" in str(error)
    else:
        raise AssertionError("unapproved plan must be rejected")
