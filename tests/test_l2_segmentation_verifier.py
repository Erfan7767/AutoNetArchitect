"""L2 component test."""
def test_l2_segmentation_verifier_imports():
    __import__("designers.l2_protocols.l2_safety.l2_segmentation_verifier" if "l2_safety" else "designers.l2_protocols.l2_orchestrator")
