from operations import MigrationPlanner, MigrationStatus


def _records():
    current = {"edge-1": {"vendor": "cisco", "platform": "ios_xe", "model": "C9300", "version": "17.6", "hostname": "edge-1", "serial": "FDO1", "status": "collected", "confidence": "high"}}
    target = {"edge-1": {"vendor": "cisco", "platform": "ios_xe", "model": "C9300", "version": "17.9", "hostname": "edge-1", "serial": "FDO1"}}
    return current, target


def test_migration_planner_creates_reviewable_brownfield_plan_without_execution_authority():
    current, target = _records()
    plan = MigrationPlanner().plan(current, target, ["edge-1"], approved_change_window="window-1", lab_validation_evidence_ids=["lab-e1"], evidence_ids=["discovery-e1"])
    assert plan.mode == "brownfield_assisted"
    assert plan.status == MigrationStatus.READY_FOR_REVIEW.value
    assert plan.production_execution_allowed is False
    assert plan.human_review_required is True
    assert plan.changed_fields["edge-1"] == ("version",)
    assert len(plan.phases) == 3


def test_migration_planner_blocks_missing_human_inputs_and_ambiguous_inventory():
    current, target = _records()
    incomplete = MigrationPlanner().plan(current, target, ["edge-1"])
    assert incomplete.status == MigrationStatus.PREVIEW_ONLY.value
    assert "approved_change_window" in incomplete.required_human_inputs
    ambiguous = {"edge-1": {**current["edge-1"], "confidence": "ambiguous"}}
    blocked = MigrationPlanner().plan(ambiguous, target, ["edge-1"])
    assert blocked.status == MigrationStatus.BLOCKED_AMBIGUOUS_INVENTORY.value
    assert blocked.production_execution_allowed is False
