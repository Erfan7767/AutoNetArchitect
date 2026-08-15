"""L2 component test."""
def test_mlag_vpc_designer_imports():
    __import__("designers.l2_protocols.port_channel.mlag_vpc_designer" if "port_channel" else "designers.l2_protocols.l2_orchestrator")
