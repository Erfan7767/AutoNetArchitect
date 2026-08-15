from incident_response.containment_planner import ContainmentPlanner
from incident_response.incident_models import IncidentCategory, IncidentSeverity


def test_containment_planner_is_approval_gated_and_non_executing():
    result = ContainmentPlanner().plan(incident_id="INC-20260814-0001", category=IncidentCategory.SECURITY_INCIDENT, severity=IncidentSeverity.P1_CRITICAL, preserve_evidence=True)
    assert result.execution_allowed is False
    assert result.preserves_evidence is True
    assert all(step.requires_approval for step in result.steps)


def test_containment_planner_rejects_evidence_disabling():
    try:
        ContainmentPlanner().plan(incident_id="INC-20260814-0001", category=IncidentCategory.NETWORK_OUTAGE, severity=IncidentSeverity.P2_HIGH, preserve_evidence=False)
    except ValueError as error:
        assert "evidence" in str(error)
    else:
        raise AssertionError("evidence disabling must be rejected")
