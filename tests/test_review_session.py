import tempfile
from audit.audit_trail import AuditTrail
from review_console.review_session import ReviewSession, ReviewSessionManager, ReviewSessionStatus

def test_review_session_tracks_human_actions_and_audit():
    with tempfile.NamedTemporaryFile(suffix=".jsonl") as handle:
        audit = AuditTrail(handle.name)
        manager = ReviewSessionManager(audit_trail=audit)
        session = manager.start(ReviewSession(session_id="session-1", project_id="p-1", workflow="design", reviewer_id="eng-1", reviewer_role="technical_reviewer"))
        manager.record_event(session.session_id, actor_id="eng-1", actor_role="technical_reviewer", action="reviewed_alternatives", note="option a retained")
        updated = manager.update_status(session.session_id, ReviewSessionStatus.SUBMITTED, actor_id="eng-1", actor_role="technical_reviewer", note="submitted for approval")
        assert updated.status == ReviewSessionStatus.SUBMITTED and len(manager.events(session.session_id)) == 2 and audit.query(event_type="review_console.session")
