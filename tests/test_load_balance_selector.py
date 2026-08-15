"""L2 component test."""
def test_load_balance_selector_imports():
    __import__("designers.l2_protocols.port_channel.load_balance_selector" if "port_channel" else "designers.l2_protocols.l2_orchestrator")
