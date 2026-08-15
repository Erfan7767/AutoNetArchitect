from equipment.capability_matrix import CapabilityMatrix, CapabilityRecord


def test_capability_requires_verified_evidence_chain():
    matrix = CapabilityMatrix(
        [CapabilityRecord("AcmeNet", "switch", "X1", "routing", "1.0", "2.0", ("advanced",), "supported_with_license", ("ev-routing",), ("src-lab",), 0.93)],
        {"ev-routing": {"source_id": "src-lab", "verification_state": "verified", "revoked": False, "expired": False}},
        {"src-lab": {"verified": True}},
    )
    result = matrix.supports("AcmeNet", "switch", "X1", "1.5", "routing", "advanced")
    assert result.supported is True
    assert result.evidence_chain == ("ev-routing",)


def test_unverified_capability_is_not_a_support_claim():
    matrix = CapabilityMatrix([CapabilityRecord("AcmeNet", "switch", "X1", "routing", support_state="supported", evidence_ids=("missing",), confidence=0.8)])
    result = matrix.supports("AcmeNet", "switch", "X1", None, "routing")
    assert result.supported is False
    assert result.reason == "capability_evidence_missing_or_not_verified"
