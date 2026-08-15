from governance.accountability_matrix import AccountabilityMatrix, DecisionClass, RiskClass
from governance.signoff_policy import CheckpointRecord, CheckpointType, SignoffPolicy
from governance.review_classes import ReviewOutcome

def _full_checkpoints(requirement):
    records = []
    for index, role in enumerate(requirement.required_reviewer_roles):
        records.append(CheckpointRecord(checkpoint_id=f"r-{index}", workflow=requirement.workflow, checkpoint_type=CheckpointType.REVIEW, principal_id=f"reviewer-{index}", role=role, outcome=ReviewOutcome.ACCEPTED, rationale="technical evidence reviewed"))
    for index, role in enumerate(requirement.required_approver_roles):
        records.append(CheckpointRecord(checkpoint_id=f"a-{index}", workflow=requirement.workflow, checkpoint_type=CheckpointType.APPROVAL, principal_id=f"approver-{index}", role=role, outcome=ReviewOutcome.ACCEPTED, rationale="approval granted", reference=f"approval://a-{index}"))
    records.append(CheckpointRecord(checkpoint_id="owner", workflow=requirement.workflow, checkpoint_type=CheckpointType.ACCOUNTABILITY, principal_id="owner-1", role=requirement.accountable_owner_role, outcome=ReviewOutcome.ACCEPTED, rationale="accountability accepted", reference="owner://deployment"))
    for index, role in enumerate(requirement.execution_authority_roles):
        records.append(CheckpointRecord(checkpoint_id=f"x-{index}", workflow=requirement.workflow, checkpoint_type=CheckpointType.EXECUTION_AUTHORITY, principal_id=f"executor-{index}", role=role, outcome=ReviewOutcome.ACCEPTED, rationale="execution authority granted", reference=f"approval://x-{index}"))
    return records

def test_signoff_policy_blocks_missing_human_checkpoints():
    requirement = AccountabilityMatrix().resolve(workflow="deployment", decision_class=DecisionClass.DEPLOYMENT, risk_class=RiskClass.CRITICAL)
    result = SignoffPolicy().evaluate(requirement, [])
    assert result.allowed is False and result.pending_checkpoints

def test_signoff_policy_allows_complete_distinct_checkpoints():
    requirement = AccountabilityMatrix().resolve(workflow="deployment", decision_class=DecisionClass.DEPLOYMENT, risk_class=RiskClass.CRITICAL)
    result = SignoffPolicy().evaluate(requirement, _full_checkpoints(requirement))
    assert result.allowed is True and result.state == "approved"
