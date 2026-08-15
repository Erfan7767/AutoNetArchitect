from change_management import ChangeRequest, ChangeVerificationEngine, VerificationResult


def test_change_verification_engine_aggregates_passed_results():
    request = ChangeRequest("CHG-14", "Verify", "Detailed", "alice", status="verification")
    result = ChangeVerificationEngine().verify(request, [VerificationResult("v1", "command_verification", "show", "up", "up", "passed", evidence_ids=("v-e1",))])
    assert result.overall_status == "passed"
    assert result.rollback_consideration_required is False
    assert request.status == "completed"


def test_change_verification_engine_triggers_rollback_consideration_on_failure():
    request = ChangeRequest("CHG-15", "Verify", "Detailed", "alice", status="verification")
    result = ChangeVerificationEngine().verify(request, [{"verification_id": "v1", "verification_type": "connectivity_verification", "command_or_action": "ping", "expected_result": "reachable", "actual_result": "unreachable", "status": "failed"}])
    assert result.overall_status == "failed"
    assert result.rollback_consideration_required is True
    assert request.status == "failed"
