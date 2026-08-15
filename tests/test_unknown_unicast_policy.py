"""L2 component test."""
def test_unknown_unicast_policy_imports():
    __import__("designers.l2_protocols.l2_safety.unknown_unicast_policy" if "l2_safety" else "designers.l2_protocols.l2_orchestrator")
