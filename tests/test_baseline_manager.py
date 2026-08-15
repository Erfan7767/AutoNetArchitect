from traffic_analysis.baseline_manager import BaselineManager

def test_baseline_manager_calculates_statistics_and_comparison():
    manager = BaselineManager()
    baseline = manager.create(subject_id="l1", metric="utilization", period_label="business_hours", values=[10,20,30,40], evidence_ids=["ev-1"])
    assert baseline.percentile_95 is not None
    comparison = manager.compare(baseline, current_value=100)
    assert comparison["anomalous"] is True
