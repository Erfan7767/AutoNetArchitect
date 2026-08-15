from datetime import timedelta
from traffic_analysis.wan_utilization_analyzer import WANUtilizationAnalyzer
from traffic_analysis.models import LinkType, TrafficData, TrafficLinkModel, TrafficSource

def test_wan_analyzer_filters_wan_and_evaluates_peak():
    link = TrafficLinkModel(link_id="wan1", source_device="r1", source_interface="i", destination_device="isp", destination_interface="i", link_speed_mbps=1000, link_type=LinkType.WAN_LINK, traffic_data=TrafficData(source=TrafficSource.COLLECTED, avg_utilization_percent=50, peak_utilization_percent=92, measurement_period=timedelta(minutes=5), evidence_ids=["ev-1"], confidence=0.9))
    result = WANUtilizationAnalyzer().analyze([link])
    assert result[0].status.value == "upgrade_required"
