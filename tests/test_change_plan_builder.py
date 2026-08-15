from change_management import ChangePlanBuilder, ChangeRequest, ConfigChange


def test_change_plan_builder_uses_supplied_commands_and_validator():
    request = ChangeRequest("CHG-5", "Config", "Detailed", "alice", config_changes=[ConfigChange("edge-1", "edge-1", "interface", "old", "new", "diff", ("set command",), ("rollback command",), validator_evidence_ids=("val-1",))])
    plan = ChangePlanBuilder().build(request, validator=lambda device, commands: device == "edge-1" and commands == ("set command",))
    assert len(plan.steps) == 1
    assert plan.steps[0].commands == ("set command",)
    assert plan.steps[0].rollback_commands == ("rollback command",)
    assert plan.validator_evidence_ids == ("val-1",)
    assert request.implementation_plan == plan
