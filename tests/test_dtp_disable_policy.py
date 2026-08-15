"""L2 component test."""
def test_dtp_disable_policy_imports():
    __import__("designers.l2_protocols.trunk.dtp_disable_policy" if "trunk" else "designers.l2_protocols.l2_orchestrator")
