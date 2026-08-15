"""L2 component test."""
def test_lacp_policy_imports():
    __import__("designers.l2_protocols.port_channel.lacp_policy" if "port_channel" else "designers.l2_protocols.l2_orchestrator")
