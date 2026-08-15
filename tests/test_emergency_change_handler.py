from change_management import ChangeRequest, EmergencyChangeHandler


def test_emergency_change_handler_requires_controls_and_sets_followup_deadlines():
    request = ChangeRequest("CHG-29", "Outage restore", "Detailed", "alice", change_type="emergency")
    assessment = EmergencyChangeHandler().declare(request, justification="restore active outage", criteria=["service_outage"], on_call_approval=True, backup_evidence_ids=["backup-1"])
    assert assessment.allowed_to_start is True
    assert assessment.review_due > assessment.documentation_due
    assert any("24 hours" in item for item in assessment.required_controls)


def test_emergency_change_handler_blocks_missing_backup():
    request = ChangeRequest("CHG-30", "Outage restore", "Detailed", "alice", change_type="emergency")
    assessment = EmergencyChangeHandler().declare(request, justification="restore active outage", criteria=["service_outage"], on_call_approval=True)
    assert assessment.allowed_to_start is False
    assert any("backup" in reason for reason in assessment.reasons)
