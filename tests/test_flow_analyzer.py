from traffic_analysis.flow_analyzer import FlowAnalyzer
from traffic_analysis.models import FlowRecord

def test_flow_analyzer_reports_top_talkers():
    flow = FlowRecord(source_ip="10.0.0.1", destination_ip="10.0.0.2", protocol="tcp", destination_port=443, bytes_count=1000, source_subnet="10.0.0.0/24", destination_subnet="10.0.1.0/24", application="web", evidence_id="ev-1")
    result = FlowAnalyzer().analyze([flow])
    assert result.available is True
    assert result.top_source_ips[0]["source_ip"] == "10.0.0.1"

def test_flow_analyzer_marks_missing_flow_data():
    result = FlowAnalyzer().analyze([])
    assert result.available is False
    assert result.assumptions
