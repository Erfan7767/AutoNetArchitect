from supervised_mode.block_gate import BlockGate
from supervised_mode.supervision_context import SupervisionContext
from supervised_mode.supervision_policy import SupervisionPolicy
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowMode, WorkflowStage

def test_block_gate_records_block_and_never_continues():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.PREVIEW, human_owner_id="eng-1", current_stage=WorkflowStage.DEPLOYMENT_EXECUTION)
    evaluation = SupervisionPolicy().evaluate("deployment.execution_gate", context, evidence_ids=("ev-1",), mutating=True)
    updated, result = BlockGate().evaluate(evaluation, context, evidence_ids=("ev-1",))
    assert result.decision == SupervisionDecision.BLOCKED and result.continued is False and len(updated.events) == 1
