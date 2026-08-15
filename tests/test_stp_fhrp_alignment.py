"""L2 component test."""
def test_stp_fhrp_alignment_imports():
    __import__("designers.l2_protocols.stp.stp_fhrp_alignment" if "stp" else "designers.l2_protocols.l2_orchestrator")
