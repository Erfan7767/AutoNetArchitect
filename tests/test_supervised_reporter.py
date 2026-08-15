from supervised_mode.supervised_reporter import SupervisedReporter
from supervised_mode.supervision_context import SupervisionContext, SupervisionEvent
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowMode, WorkflowStage

def test_supervised_reporter_summarizes_human_intervention():
    context = SupervisionContext(project_id="p-1", workflow_run_id="r-1", mode=WorkflowMode.SUPERVISED, high_assurance=True, human_owner_id="eng-1", sot_basis={"DESIGN": "sot://design/p-1"}, events=(SupervisionEvent(event_id="e-1", checkpoint_id="design.intent_review", workflow_stage=WorkflowStage.DESIGN, decision=SupervisionDecision.REQUIRES_REVIEW, actor_id="system"), SupervisionEvent(event_id="e-2", checkpoint_id="deployment.execution_gate", workflow_stage=WorkflowStage.DEPLOYMENT_EXECUTION, decision=SupervisionDecision.AUTO_CONTINUE, actor_id="eng-1", actor_role="deployment_approver", action="approve", reference="approval://deploy")))
    report = SupervisedReporter().generate(context)
    assert report.human_intervention_count == 2 and report.requires_review_count == 1 and report.sot_basis["DESIGN"] == "sot://design/p-1"
    assert "Human Intervention Summary" in SupervisedReporter().to_markdown(report)
