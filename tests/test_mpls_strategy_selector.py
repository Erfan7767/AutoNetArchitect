from designers.mpls.mpls_strategy_selector import MPLSStrategySelector
def test_missing_offering(): assert MPLSStrategySelector().design({})["status"]=="blocked_missing_human_data"
