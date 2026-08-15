from supervised_mode.approval_gate import ApprovalGate
from supervised_mode.supervision_context import SupervisionContext
from supervised_mode.supervision_policy import SupervisionPolicy
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowMode, WorkflowStage

def test_approval_gate_requires_reference():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.SUPERVISED, human_owner_id="eng-1", current_stage=WorkflowStage.DEPLOYMENT_EXECUTION)
    evaluation = SupervisionPolicy().evaluate("deployment.execution_gate", context, evidence_ids=("ev-1",), mutating=True)
    _, result = ApprovalGate().evaluate(evaluation, context, approver_id="approver-1", approver_role="deployment_approver", action="approve", rationale="change approved")
    assert result.decision == SupervisionDecision.REQUIRES_APPROVAL and result.continued is False

def test_approval_gate_records_approval_reference():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.SUPERVISED, human_owner_id="eng-1", current_stage=WorkflowStage.DEPLOYMENT_EXECUTION)
    evaluation = SupervisionPolicy().evaluate("deployment.execution_gate", context, evidence_ids=("ev-1",), mutating=True)
    updated, result = ApprovalGate().evaluate(evaluation, context, approver_id="approver-1", approver_role="deployment_approver", approval_reference="approval://deploy/r-1", action="approve", rationale="backup and rollback reviewed", evidence_ids=("ev-1",))
    assert result.continued is True and updated.events[0].reference.startswith("approval://")
