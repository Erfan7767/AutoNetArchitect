from datetime import timedelta
from traffic_analysis.bandwidth_calculator import BandwidthCalculator
from traffic_analysis.models import LinkType, TrafficData, TrafficLinkModel, TrafficSource

def test_bandwidth_calculator_detects_upgrade_need():
    link = TrafficLinkModel(link_id="l1", source_device="a", source_interface="i", destination_device="b", destination_interface="i", link_speed_mbps=10, link_type=LinkType.WAN_LINK, traffic_data=TrafficData(source=TrafficSource.COLLECTED, peak_bps_in=20_000_000, peak_bps_out=20_000_000, measurement_period=timedelta(minutes=5), evidence_ids=["ev-1"], confidence=0.9))
    result = BandwidthCalculator().calculate_link(link)
    assert result.upgrade_needed is True
    assert result.required_bandwidth_mbps > 10
