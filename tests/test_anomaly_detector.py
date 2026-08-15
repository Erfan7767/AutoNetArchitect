from traffic_analysis.anomaly_detector import AnomalyDetector
from traffic_analysis.baseline_manager import BaselineManager

def test_anomaly_detector_detects_spike_from_baseline():
    baseline = BaselineManager().create(subject_id="l1", metric="utilization", period_label="all", values=[10,11,9,10], evidence_ids=["ev-1"])
    result = AnomalyDetector().detect(subject_id="l1", metric="utilization", baseline=baseline, current_value=100)
    assert result
    assert result[0].anomaly_type.value == "traffic_spike"

def test_anomaly_detector_marks_missing_baseline():
    detector = AnomalyDetector()
    assert detector.detect(subject_id="l1", metric="utilization", baseline=None, current_value=1) == []
    assert detector.assumptions
