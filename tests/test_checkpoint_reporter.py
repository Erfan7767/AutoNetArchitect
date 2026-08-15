from review_control.checkpoint_reporter import CheckpointReporter
from review_control.mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointStatus

def test_checkpoint_reporter_shows_unresolved_checkpoints():
    report = CheckpointReporter().generate(project_id="p-1")
    assert report.release_blocked and report.unresolved_checkpoint_ids
    assert "Mandatory Checkpoint Report" in CheckpointReporter().to_markdown(report)

def test_checkpoint_reporter_can_show_resolved_requirements():
    record = CheckpointRecord(checkpoint_id="requirements.completeness_review", workflow_stage="requirements", status=MandatoryCheckpointStatus.RESOLVED, reviewer_id="reviewer", reviewer_role="technical_reviewer", evidence_ids=("req-1",))
    report = CheckpointReporter().generate(project_id="p-1", records=(record,))
    row = next(item for item in report.checkpoints if item["checkpoint_id"] == "requirements.completeness_review")
    assert row["release_ready"] is True
