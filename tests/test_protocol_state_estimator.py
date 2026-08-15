from digital_twin import ProtocolStateEstimator, StateCertainty


def test_protocol_state_estimator_separates_observed_and_inferred_states():
    estimator = ProtocolStateEstimator()
    observed = estimator.estimate("edge-1", "bgp", {"protocol_state": "established", "neighbor": "192.0.2.1"}, evidence_ids=["bgp-1"])
    assert observed.certainty == StateCertainty.OBSERVED.value
    assert observed.state == "established"
    inferred = estimator.estimate("edge-1", "ospf", {"neighbor_state": "full", "keepalive": True}, inference_rules={"full": {"neighbor_state": "full", "keepalive": True}}, evidence_ids=["ospf-1"])
    assert inferred.certainty == StateCertainty.INFERRED.value
    assert inferred.inference_rule == "rule:full"
    assert "protocol emulation" in inferred.limitations[0]


def test_protocol_state_estimator_marks_multiple_matches_ambiguous():
    result = ProtocolStateEstimator().estimate("edge-1", "bgp", {"neighbor_state": "up"}, inference_rules={"established": {"neighbor_state": "up"}, "active": {"neighbor_state": "up"}})
    assert result.certainty == StateCertainty.AMBIGUOUS.value
    assert result.state == "ambiguous"
