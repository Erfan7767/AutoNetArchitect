"""L2 component test."""
def test_access_port_designer_imports():
    __import__("designers.l2_protocols.access_port.access_port_designer" if "access_port" else "designers.l2_protocols.l2_orchestrator")
