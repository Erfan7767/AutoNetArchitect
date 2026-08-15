from datetime import datetime, timedelta, timezone
from governance.exception_waiver_model import ExceptionWaiverRegistry, WaiverRequest, WaiverStatus
from governance.accountability_matrix import RiskClass

def _waiver():
    return WaiverRequest(waiver_id="W-1", workflow="deployment", boundary_or_policy="scope-boundary", risk_class=RiskClass.HIGH, requester_id="alice", accountable_owner_id="owner", rationale="temporary vendor limitation", impact_if_granted="reduced validation", compensating_controls=("manual review",), validation_plan=("lab validation",), reviewer_references=("review://sec/W-1",), expires_at=datetime.now(timezone.utc) + timedelta(hours=2))

def test_waiver_registry_requires_controls_and_review():
    request = _waiver().model_copy(update={"compensating_controls": (), "validation_plan": (), "reviewer_references": ()})
    result = ExceptionWaiverRegistry().submit(request)
    assert result.status == WaiverStatus.REJECTED and result.enforceable is False

def test_waiver_registry_approves_and_expires():
    registry = ExceptionWaiverRegistry()
    registry.submit(_waiver())
    approved = registry.approve("W-1", approver_reference="approval://waiver/W-1", rationale="risk accepted temporarily")
    assert approved.enforceable is True
    assert registry.assessment("W-1").status == WaiverStatus.APPROVED
    registry.revoke("W-1", "control restored")
    assert registry.assessment("W-1").status == WaiverStatus.REVOKED
