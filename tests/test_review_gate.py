from supervised_mode.review_gate import ReviewGate
from supervised_mode.supervision_context import SupervisionContext
from supervised_mode.supervision_policy import SupervisionPolicy
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowMode, WorkflowStage

def test_review_gate_waits_for_human_reviewer():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.SUPERVISED, human_owner_id="eng-1", current_stage=WorkflowStage.DESIGN)
    evaluation = SupervisionPolicy().evaluate("design.intent_review", context, evidence_ids=("ev-1",))
    updated, result = ReviewGate().evaluate(evaluation, context)
    assert result.decision == SupervisionDecision.REQUIRES_REVIEW and result.continued is False and updated.events == ()

def test_review_gate_records_accepted_review():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.SUPERVISED, human_owner_id="eng-1", current_stage=WorkflowStage.DESIGN)
    evaluation = SupervisionPolicy().evaluate("design.intent_review", context, evidence_ids=("ev-1",))
    updated, result = ReviewGate().evaluate(evaluation, context, reviewer_id="reviewer-1", reviewer_role="technical_reviewer", action="accept", rationale="decision and alternatives reviewed", evidence_ids=("ev-1",))
    assert result.continued is True and len(updated.events) == 1
