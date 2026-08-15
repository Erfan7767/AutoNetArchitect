from designers.fhrp.fhrp_orchestrator import FHRPOrchestrator
def test_orchestrator(): assert FHRPOrchestrator().design({"vendors":["Cisco"],"vlans":[]})["status"]=="designed"
