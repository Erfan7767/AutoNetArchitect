from designers.nat.nat_strategy_selector import NATStrategySelector
def test_dual_isp_policy(): assert "policy_nat" in NATStrategySelector().design({"internet_access":True,"dual_isp":True})["strategies"]
