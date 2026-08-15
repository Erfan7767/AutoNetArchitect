from datetime import timedelta
from traffic_analysis.bottleneck_detector import BottleneckDetector
from traffic_analysis.models import LinkType, TrafficData, TrafficLinkModel, TrafficSource

def test_bottleneck_detector_detects_high_utilization():
    link = TrafficLinkModel(link_id="l1", source_device="a", source_interface="i", destination_device="b", destination_interface="i", link_speed_mbps=1000, link_type=LinkType.CORE_LINK, traffic_data=TrafficData(source=TrafficSource.COLLECTED, peak_utilization_percent=95, measurement_period=timedelta(minutes=5), evidence_ids=["ev-1"], confidence=0.9))
    result = BottleneckDetector().detect([link])
    assert result[0].bottleneck_type.value == "bandwidth_bottleneck"
    assert result[0].severity.value == "critical"
