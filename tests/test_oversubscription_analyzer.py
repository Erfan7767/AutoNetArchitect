from traffic_analysis.oversubscription_analyzer import OversubscriptionAnalyzer

def test_oversubscription_analyzer_detects_critical_ratio():
    result = OversubscriptionAnalyzer().analyze(subject_id="uplink", tier="access_to_distribution", downstream_capacities_mbps=[1000]*30, uplink_capacity_mbps=1000)
    assert result.ratio == 30
    assert result.status.value == "upgrade_required"

def test_oversubscription_analyzer_marks_unknown_guideline():
    result = OversubscriptionAnalyzer().analyze(subject_id="uplink", tier="unknown_tier", downstream_capacities_mbps=[100], uplink_capacity_mbps=100, domain="unknown")
    assert result.status.value == "unknown"
