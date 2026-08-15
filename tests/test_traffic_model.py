from datetime import timedelta
from traffic_analysis.models import LinkType, TrafficData, TrafficSource
from traffic_analysis.traffic_model import TrafficModelRegistry

def test_traffic_model_requires_explicit_link_and_source():
    data = TrafficData(source=TrafficSource.COLLECTED, avg_bps_in=1000, avg_bps_out=1000, peak_bps_in=2000, peak_bps_out=2000, measurement_period=timedelta(minutes=5), evidence_ids=["ev-1"], confidence=0.9)
    link = TrafficModelRegistry().create_link(link_id="l1", source_device="a", source_interface="Gi1", destination_device="b", destination_interface="Gi1", link_speed_mbps=1000, link_type=LinkType.ACCESS_UPLINK, traffic_data=data)
    assert link.link_id == "l1"
    assert link.traffic_data.source == TrafficSource.COLLECTED

def test_traffic_model_rejects_empty_identity():
    registry = TrafficModelRegistry()
    try:
        registry.create_link(link_id="", source_device="a", source_interface="Gi1", destination_device="b", destination_interface="Gi1", link_speed_mbps=1000, link_type=LinkType.ACCESS_UPLINK, traffic_data=TrafficData(source=TrafficSource.ESTIMATED, assumptions=["assumption"]))
    except ValueError:
        return
    raise AssertionError("empty link identity must be rejected")
