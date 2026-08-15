from incident_response.recovery_planner import RecoveryPlanner


def test_recovery_planner_orders_core_before_access():
    result = RecoveryPlanner().plan(incident_id="INC-20260814-0001", services=[{"service_id":"access", "tier":"access"}, {"service_id":"core", "tier":"core"}])
    assert [step.service_id for step in result.services] == ["core", "access"]
    assert result.execution_allowed is False


def test_recovery_planner_marks_missing_services():
    result = RecoveryPlanner().plan(incident_id="INC-20260814-0001", services=[])
    assert result.assumptions
