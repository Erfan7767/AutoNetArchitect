from discovery import ReconciliationEngine


def test_reconciliation_reports_aligned_when_lifecycle_identity_matches():
    record = {"vendor": "cisco", "platform": "ios_xe", "model": "C9300", "version": "17.9.4", "serial": "FDO123", "hostname": "core-1", "evidence_ids": ["e1"]}
    report = ReconciliationEngine().reconcile(design={"asset-1": record}, installed={"asset-1": record}, discovered={"asset-1": record}, operational={"asset-1": {**record, "attributes": {"healthy": True}}})
    assert report.status == "aligned"
    assert report.production_gate == "allow"
    assert report.findings[-1].status == "aligned"


def test_reconciliation_blocks_drift_missing_and_unexpected_assets():
    report = ReconciliationEngine().reconcile(
        design={"asset-1": {"vendor": "cisco", "model": "C9300"}},
        discovered={"asset-1": {"vendor": "cisco", "model": "C9300-48", "status": "collected"}, "asset-2": {"vendor": "aruba", "model": "JL658A", "status": "collected"}},
    )
    statuses = {finding.status for finding in report.findings}
    assert "drift" in statuses
    assert "unexpected_discovered" in statuses
    assert report.production_gate == "block_or_review"
