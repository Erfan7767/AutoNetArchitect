from operations import PartialRollbackPlanner, RollbackStatus


def _configs():
    return {"edge-1": "baseline-hash-1", "edge-2": "baseline-hash-2"}, {"edge-1": "current-hash-1", "edge-2": "current-hash-2"}


def test_partial_rollback_creates_scoped_review_plan_and_preserves_controls():
    baseline, current = _configs()
    plan = PartialRollbackPlanner().plan(["edge-1", "edge-2"], ["edge-1"], baseline, current, approved_change_window="window-1", validation_evidence_ids=["lab-rb-1"], evidence_ids=["cfg-e1"])
    assert plan.status == RollbackStatus.READY_FOR_REVIEW.value
    assert plan.scope == ("edge-1",)
    assert plan.production_execution_allowed is False
    assert plan.safety_policies_preserved["preserve_management_access"] is True
    assert all("management_access" in " ".join(step.safety_checks) or step.step_id == "rollback-restore" for step in plan.steps)


def test_partial_rollback_blocks_out_of_scope_and_disabled_safety_policy():
    baseline, current = _configs()
    out_of_scope = PartialRollbackPlanner().plan(["edge-1"], ["edge-2"], baseline, current)
    assert out_of_scope.status == RollbackStatus.BLOCKED_POLICY_VIOLATION.value
    disabled = PartialRollbackPlanner().plan(["edge-1"], ["edge-1"], baseline, current, safety_policies={"preserve_segmentation": False})
    assert disabled.status == RollbackStatus.BLOCKED_POLICY_VIOLATION.value
    assert disabled.production_execution_allowed is False
