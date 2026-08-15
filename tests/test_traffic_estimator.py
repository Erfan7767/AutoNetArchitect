from traffic_analysis.traffic_estimator import TrafficEstimator
from traffic_analysis.models import LinkType, TrafficSource

def test_traffic_estimator_marks_estimate_and_assumption():
    link = TrafficEstimator().estimate_link(link_id="l1", source_device="a", source_interface="Gi1", destination_device="b", destination_interface="Gi1", link_speed_mbps=1000, link_type=LinkType.ACCESS_UPLINK, user_profile_counts={"office_worker": 20})
    assert link.traffic_data.source == TrafficSource.ESTIMATED
    assert link.traffic_data.assumptions
    assert link.users_served == 20

def test_traffic_estimator_rejects_unknown_profile():
    try:
        TrafficEstimator().estimate_link(link_id="l1", source_device="a", source_interface="Gi1", destination_device="b", destination_interface="Gi1", link_speed_mbps=1000, link_type=LinkType.ACCESS_UPLINK, user_profile_counts={"invented": 1})
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError("unknown traffic profile must be blocked")
