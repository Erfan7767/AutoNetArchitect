from designers.dr_bc.dr_strategy_selector import DRStrategySelector
def test_tier_mapping(): assert DRStrategySelector().design({'tier':'tier1','existing_dr_infrastructure':True})['strategy']=='active_active'
