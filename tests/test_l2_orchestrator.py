from designers.l2_protocols.l2_orchestrator import L2Orchestrator
def test_order():
    result=L2Orchestrator().design({"allowed_vlans":[10,20]}); assert result["consistency"]=="checked"
