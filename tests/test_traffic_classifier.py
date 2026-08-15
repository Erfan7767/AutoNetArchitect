from traffic_analysis.traffic_classifier import TrafficClassifier
from traffic_analysis.models import FlowRecord, TrafficPriorityClass

def test_traffic_classifier_uses_port_and_direction():
    flow = FlowRecord(source_ip="10.0.0.1", destination_ip="10.0.0.2", protocol="tcp", destination_port=443, bytes_count=100, evidence_id="ev-1")
    result = TrafficClassifier().classify(flow, source_zone="user", destination_zone="server")
    assert result.application == "web"
    assert result.priority_class == TrafficPriorityClass.DEFAULT
    assert result.direction.value == "north_south"

def test_traffic_classifier_marks_unknown_without_evidence():
    flow = FlowRecord(source_ip="10.0.0.1", destination_ip="10.0.0.2", protocol="udp", destination_port=9999, bytes_count=100, evidence_id="ev-1")
    result = TrafficClassifier().classify(flow)
    assert result.assumptions
