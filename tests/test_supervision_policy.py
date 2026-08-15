from supervised_mode.checkpoint_registry import CheckpointRegistry
from supervised_mode.supervision_context import SupervisionContext
from supervised_mode.supervision_policy import SupervisionPolicy
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowMode, WorkflowStage

def _context():
    return SupervisionContext(project_id="p-1", workflow_run_id="run-1", mode=WorkflowMode.SUPERVISED, human_owner_id="eng-1", current_stage=WorkflowStage.DEPLOYMENT_EXECUTION)

def test_supervision_policy_returns_requires_approval_for_execution():
    evaluation = SupervisionPolicy().evaluate("deployment.execution_gate", _context(), evidence_ids=("ev-1",), mutating=True)
    assert evaluation.decision == SupervisionDecision.REQUIRES_APPROVAL

def test_supervision_policy_blocks_mutation_in_preview():
    context = _context().model_copy(update={"mode": WorkflowMode.PREVIEW})
    evaluation = SupervisionPolicy().evaluate("deployment.execution_gate", context, evidence_ids=("ev-1",), mutating=True)
    assert evaluation.decision == SupervisionDecision.BLOCKED
