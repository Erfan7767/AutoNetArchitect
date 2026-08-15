from governance.accountability_matrix import RiskClass
from governance.separation_of_duties import SeparationOfDutiesPolicy
from governance.signoff_policy import CheckpointRecord, CheckpointType
from governance.review_classes import ReviewOutcome

def test_separation_of_duties_detects_reviewer_approver_collision():
    records = [CheckpointRecord(checkpoint_id="r", workflow="deployment", checkpoint_type=CheckpointType.REVIEW, principal_id="same", role="technical_reviewer", outcome=ReviewOutcome.ACCEPTED, rationale="reviewed"), CheckpointRecord(checkpoint_id="a", workflow="deployment", checkpoint_type=CheckpointType.APPROVAL, principal_id="same", role="deployment_approver", outcome=ReviewOutcome.ACCEPTED, rationale="approved", reference="approval://a")]
    result = SeparationOfDutiesPolicy().evaluate(workflow="deployment", risk_class=RiskClass.CRITICAL, checkpoints=records)
    assert result.allowed is False and result.conflicts

def test_separation_of_duties_allows_distinct_roles():
    records = [CheckpointRecord(checkpoint_id="r", workflow="deployment", checkpoint_type=CheckpointType.REVIEW, principal_id="reviewer", role="technical_reviewer", outcome=ReviewOutcome.ACCEPTED, rationale="reviewed"), CheckpointRecord(checkpoint_id="a", workflow="deployment", checkpoint_type=CheckpointType.APPROVAL, principal_id="approver", role="deployment_approver", outcome=ReviewOutcome.ACCEPTED, rationale="approved", reference="approval://a")]
    assert SeparationOfDutiesPolicy().evaluate(workflow="deployment", risk_class=RiskClass.CRITICAL, checkpoints=records).allowed
