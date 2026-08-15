"""L2 component test."""
def test_l2_loop_prevention_imports():
    __import__("designers.l2_protocols.l2_safety.l2_loop_prevention" if "l2_safety" else "designers.l2_protocols.l2_orchestrator")
