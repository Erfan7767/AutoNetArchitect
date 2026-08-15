from designers.nat.nat_orchestrator import NATOrchestrator
def test_orchestration(): assert "pat" in NATOrchestrator().design({"internet_access":True})["strategies"]
