from designers.access_control.nac_orchestrator import NACOrchestrator
def test_regulated_nac_requires_radius(): assert NACOrchestrator().design({"regulated_domain":True})["required"]
