from review_control.no_go_policy import BlockerClass, NoGoBlocker, NoGoOutcome, NoGoPolicy

def test_no_go_policy_emits_formal_blocker_outcome():
    blocker = NoGoBlocker(blocker_id="B-1", blocker_class=BlockerClass.EVIDENCE, blocking_reason="evidence is stale", affected_stage="design", required_resolution="obtain current evidence")
    result = NoGoPolicy().evaluate(stage="design", blockers=(blocker,), production_requested=True, approval_present=True)
    assert result.outcome == NoGoOutcome.NO_GO and result.blockers[0].blocker_id == "B-1" and result.reasons

def test_no_go_policy_allows_go_with_conditions_for_review_path():
    result = NoGoPolicy().evaluate(stage="design", production_requested=False)
    assert result.outcome == NoGoOutcome.GO_WITH_CONDITIONS
