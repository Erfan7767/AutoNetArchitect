import tempfile
from audit.audit_trail import AuditTrail
from supervised_mode.supervision_context import SupervisionContextManager, SupervisionEvent
from supervised_mode.workflow_mode import SupervisionDecision, WorkflowStage

def test_context_manager_tracks_stage_event_and_audit():
    with tempfile.NamedTemporaryFile(suffix=".jsonl") as handle:
        audit = AuditTrail(handle.name)
        manager = SupervisionContextManager(audit_trail=audit)
        context = manager.create(project_id="p-1", workflow_run_id="r-1", human_owner_id="eng-1")
        context = manager.enter_stage(context, WorkflowStage.REQUIREMENTS)
        context = manager.append_event(context, SupervisionEvent(event_id="e-1", checkpoint_id="requirements.analysis_review", workflow_stage=WorkflowStage.REQUIREMENTS, decision=SupervisionDecision.REQUIRES_REVIEW, evidence_ids=("ev-1",)))
        assert context.current_stage == WorkflowStage.REQUIREMENTS and context.pending_events()
        assert len(audit.query(event_type="supervised_mode.checkpoint")) == 1
