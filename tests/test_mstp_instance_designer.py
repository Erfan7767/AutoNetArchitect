"""L2 component test."""
def test_mstp_instance_designer_imports():
    __import__("designers.l2_protocols.stp.mstp_instance_designer" if "stp" else "designers.l2_protocols.l2_orchestrator")
