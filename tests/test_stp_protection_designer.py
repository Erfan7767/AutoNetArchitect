"""L2 component test."""
def test_stp_protection_designer_imports():
    __import__("designers.l2_protocols.stp.stp_protection_designer" if "stp" else "designers.l2_protocols.l2_orchestrator")
