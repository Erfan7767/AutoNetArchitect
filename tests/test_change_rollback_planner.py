from change_management import ChangeRequest, ChangeRollbackPlanner, ConfigChange, ChangePlanBuilder


def test_change_rollback_planner_builds_reverse_steps_with_backup_evidence():
    request = ChangeRequest("CHG-6", "Config", "Detailed", "alice", config_changes=[ConfigChange("edge-1", "edge-1", "one", commands_to_apply=("one",), commands_to_rollback=("undo-one",)), ConfigChange("edge-2", "edge-2", "two", commands_to_apply=("two",), commands_to_rollback=("undo-two",))])
    ChangePlanBuilder().build(request, validator=lambda device, commands: True)
    plan = ChangeRollbackPlanner().build(request, backup_evidence_ids=("backup-1",), strategy="partial_rollback")
    assert plan.strategy == "partial_rollback"
    assert plan.steps[0].device == "edge-2"
    assert plan.backup_evidence_ids == ("backup-1",)
    assert "management_access" in plan.safety_policies_preserved
