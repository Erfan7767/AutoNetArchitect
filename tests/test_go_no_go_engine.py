from review_control.go_no_go_engine import GoNoGoEngine, NoGoEnforcedError
from review_control.mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointStatus
from review_control.no_go_policy import NoGoOutcome

def test_go_no_go_engine_blocks_missing_checkpoint():
    result = GoNoGoEngine().evaluate(stage="design", production_requested=True, approval_present=True)
    assert result.outcome == NoGoOutcome.NO_GO and "design.final_review" in result.unresolved_checkpoint_ids
    try:
        GoNoGoEngine().enforce(result)
    except NoGoEnforcedError:
        return
    raise AssertionError("no-go outcome was not enforced")

def test_go_no_go_engine_allows_resolved_review_path():
    record = CheckpointRecord(checkpoint_id="design.final_review", workflow_stage="design", status=MandatoryCheckpointStatus.APPROVED, reviewer_id="owner", reviewer_role="design_authority", decision_reference="approval://design/1", rationale="final design reviewed", evidence_ids=("ev-1",))
    result = GoNoGoEngine().evaluate(stage="design", checkpoint_records=(record,), production_requested=False)
    assert result.outcome == NoGoOutcome.GO_WITH_CONDITIONS and not result.unresolved_checkpoint_ids
