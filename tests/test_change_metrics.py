from change_management import ChangeMetrics, ChangeRequest, ChangeStatus, ClosureCode, RiskAssessment


def test_change_metrics_calculates_volume_and_success_rates():
    completed = ChangeRequest("CHG-23", "Done", "Detailed", "alice", status=ChangeStatus.COMPLETED.value, risk_assessment=RiskAssessment(2, "low"))
    failed = ChangeRequest("CHG-24", "Failed", "Detailed", "alice", status=ChangeStatus.ROLLED_BACK.value, closure_code=ClosureCode.FAILED_ROLLED_BACK.value)
    emergency = ChangeRequest("CHG-25", "Emergency", "Detailed", "alice", change_type="emergency", status=ChangeStatus.COMPLETED.value, lessons_learned="reviewed")
    report = ChangeMetrics().calculate([completed, failed, emergency])
    assert report.total_changes == 3
    assert report.by_type["emergency"] == 1
    assert report.rolled_back == 1
    assert report.emergency_rate > 0
