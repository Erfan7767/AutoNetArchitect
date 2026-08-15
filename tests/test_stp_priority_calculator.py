"""L2 component test."""
def test_stp_priority_calculator_imports():
    __import__("designers.l2_protocols.stp.stp_priority_calculator" if "stp" else "designers.l2_protocols.l2_orchestrator")
