"""L2 component test."""
def test_mac_address_table_policy_imports():
    __import__("designers.l2_protocols.l2_safety.mac_address_table_policy" if "l2_safety" else "designers.l2_protocols.l2_orchestrator")
