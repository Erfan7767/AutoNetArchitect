"""L2 component test."""
def test_dhcp_snooping_designer_imports():
    __import__("designers.l2_protocols.access_port.dhcp_snooping_designer" if "access_port" else "designers.l2_protocols.l2_orchestrator")
