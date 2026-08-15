from designers.routing.routing_strategy_selector import RoutingStrategySelector
def test_multivendor_selects_ospf():
    assert RoutingStrategySelector().design({"multi_vendor":True})["protocol"]=="ospf"
