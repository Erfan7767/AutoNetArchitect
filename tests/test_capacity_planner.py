from traffic_analysis.capacity_planner import CapacityPlanner
from traffic_analysis.traffic_estimator import TrafficEstimator

def test_capacity_planner_returns_upgrade_recommendation():
    link = TrafficEstimator().estimate_link(link_id="l1", source_device="a", source_interface="i", destination_device="b", destination_interface="i", link_speed_mbps=1, link_type="access_uplink", user_profile_counts={"camera":1})
    plan = CapacityPlanner().plan(links=[link], required_by_link={"l1":10})
    assert plan.recommendations[0].target_capacity_mbps == 10
    assert plan.budget_estimate == "unknown"
