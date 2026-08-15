"""L2 component test."""
def test_ipsg_designer_imports():
    __import__("designers.l2_protocols.access_port.ipsg_designer" if "access_port" else "designers.l2_protocols.l2_orchestrator")
