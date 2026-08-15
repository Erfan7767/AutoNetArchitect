from incident_response.eradication_planner import EradicationPlanner
from incident_response.incident_models import IncidentCategory


def test_eradication_planner_requires_governance():
    result = EradicationPlanner().plan(incident_id="INC-20260814-0001", category=IncidentCategory.CONFIGURATION_ERROR, root_cause="wrong ACL", root_cause_confidence=0.8)
    assert result.execution_allowed is False
    assert result.steps[0].requires_approval is True
    assert result.assumptions


def test_eradication_planner_blocks_low_confidence_specific_fix():
    result = EradicationPlanner().plan(incident_id="INC-20260814-0001", category=IncidentCategory.HARDWARE_FAILURE, root_cause="unknown", root_cause_confidence=0.1)
    assert result.remediation_type == "investigation_required"
