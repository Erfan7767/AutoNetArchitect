from review_control.mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointStatus
from review_control.stage_release_control import StageReleaseController, StageReleaseRequest

def test_stage_release_control_blocks_unresolved_requirements():
    request = StageReleaseRequest(stage="requirements", release_target="design", production_requested=False)
    try:
        StageReleaseController().release(request)
    except RuntimeError as error:
        assert "NO-GO" in str(error)
        return
    raise AssertionError("stage release bypassed unresolved mandatory checkpoint")

def test_stage_release_control_releases_resolved_requirements():
    record = CheckpointRecord(checkpoint_id="requirements.completeness_review", workflow_stage="requirements", status=MandatoryCheckpointStatus.RESOLVED, reviewer_id="reviewer", reviewer_role="technical_reviewer", rationale="complete", evidence_ids=("req-1",))
    result = StageReleaseController().release(StageReleaseRequest(stage="requirements", release_target="design", checkpoint_records=(record,), production_requested=False))
    assert result.production_release_allowed and result.outcome.value == "go_with_conditions"
