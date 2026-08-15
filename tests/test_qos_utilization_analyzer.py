from traffic_analysis.qos_utilization_analyzer import QoSUtilizationAnalyzer

def test_qos_analyzer_detects_queue_drops():
    result = QoSUtilizationAnalyzer().analyze([{"interface_id":"i", "queue_or_class":"voice", "bandwidth_allocated_mbps":10, "bandwidth_consumed_mbps":5, "packets_dropped":3}])
    assert result[0].status.value == "upgrade_required"

def test_qos_analyzer_marks_missing_values_unknown():
    result = QoSUtilizationAnalyzer().analyze([{"interface_id":"i", "queue_or_class":"voice"}])
    assert result[0].status.value == "unknown"
