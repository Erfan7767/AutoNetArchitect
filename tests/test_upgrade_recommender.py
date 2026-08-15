from traffic_analysis.upgrade_recommender import UpgradeRecommender

def test_upgrade_recommender_uses_supported_capacity_step():
    result = UpgradeRecommender().recommend(subject_id="l1", current_capacity_mbps=1, required_capacity_mbps=8)
    assert result.target_capacity_mbps == 10
    assert result.production_approval_required is True

def test_upgrade_recommender_blocks_missing_capacity():
    result = UpgradeRecommender().recommend(subject_id="l1", current_capacity_mbps=None, required_capacity_mbps=8)
    assert result.recommended_solution == "blocked_pending_capacity_data"
