"""L2 component test."""
def test_port_security_designer_imports():
    __import__("designers.l2_protocols.access_port.port_security_designer" if "access_port" else "designers.l2_protocols.l2_orchestrator")
