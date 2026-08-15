from designers.cloud.cloud_strategy_selector import CloudStrategySelector
def test_critical_hybrid(): assert CloudStrategySelector().design({"workload_criticality":"critical","dedicated_available":True})["method"]=="hybrid"
