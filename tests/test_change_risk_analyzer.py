from change_management import ChangeRequest, ChangeRiskAnalyzer, DeviceRef, RiskLevel


def test_change_risk_analyzer_calculates_weighted_critical_risk():
    request = ChangeRequest("CHG-3", "Core migration", "Detailed", "alice", change_category="migration", affected_devices=[DeviceRef("core-1", core_infrastructure=True), DeviceRef("core-2", core_infrastructure=True)])
    result = ChangeRiskAnalyzer().analyze(request, lab_tested=False, during_maintenance_window=False, dependencies="cascading", reversibility="irreversible", complexity="migration")
    assert result.risk_level == RiskLevel.CRITICAL.value
    assert result.score >= 8
    assert result.mitigations
    assert request.status == "risk_assessed"
