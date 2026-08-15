"""L2 component test."""
def test_allowed_vlan_policy_imports():
    __import__("designers.l2_protocols.trunk.allowed_vlan_policy" if "trunk" else "designers.l2_protocols.l2_orchestrator")
