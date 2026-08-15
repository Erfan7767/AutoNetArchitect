import tempfile
from datetime import datetime, timezone
from audit.audit_trail import AuditTrail
from governance.emergency_change_policy import EmergencyChangePolicy, EmergencyChangeRequest

def test_emergency_policy_blocks_missing_recovery_and_on_call_approval():
    assessment = EmergencyChangePolicy().assess(EmergencyChangeRequest(emergency_id="E-1", requester_id="alice", justification="outage", affected_scope=("edge-1",), impact_summary="service impact"))
    assert assessment.allowed is False and "backup_reference" in assessment.required_actions

def test_emergency_policy_allows_bounded_request_and_audits():
    with tempfile.NamedTemporaryFile(suffix=".jsonl") as handle:
        audit = AuditTrail(handle.name)
        request = EmergencyChangeRequest(emergency_id="E-2", requester_id="alice", justification="active outage", affected_scope=("edge-1",), impact_summary="service impact", on_call_approval_reference="approval://oncall/E-2", override_reference="approval://override/E-2", backup_reference="backup://E-2", rollback_reference="rollback://E-2", evidence_ids=("ev-1",))
        assessment = EmergencyChangePolicy(audit_trail=audit).assess(request)
        assert assessment.allowed is True and assessment.post_implementation_review_due is not None
        assert len(audit.query(event_type="governance.emergency_change")) == 1
