from designers.routing.routing_orchestrator import RoutingOrchestrator
def test_orchestrates_single_igp():
    assert RoutingOrchestrator().design({"multi_vendor":True})["conflict_check"]=="single_igp"
