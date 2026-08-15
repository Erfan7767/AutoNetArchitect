"""L2 component test."""
def test_trunk_designer_imports():
    __import__("designers.l2_protocols.trunk.trunk_designer" if "trunk" else "designers.l2_protocols.l2_orchestrator")
