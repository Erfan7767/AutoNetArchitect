"""L2 component test."""
def test_port_channel_designer_imports():
    __import__("designers.l2_protocols.port_channel.port_channel_designer" if "port_channel" else "designers.l2_protocols.l2_orchestrator")
