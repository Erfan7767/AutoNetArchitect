from change_management import ChangeReporter, ChangeRequest, ChangeStatus, VerificationResults


def test_change_reporter_produces_individual_and_summary_reports():
    request = ChangeRequest("CHG-27", "Report", "Detailed", "alice", status=ChangeStatus.COMPLETED.value, verification_results=VerificationResults())
    reporter = ChangeReporter()
    individual = reporter.individual(request)
    assert individual.production_gate == "block_or_review"
    summary = reporter.summary([request])
    assert summary["metrics"]["total_changes"] == 1
    dashboard = reporter.dashboard([request])
    assert "risk_distribution" in dashboard
    compliance = reporter.compliance_audit([request])
    assert request.change_id in compliance["missing_rollback_plan"]
