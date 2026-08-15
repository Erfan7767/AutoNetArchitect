from digital_twin import DriftEvent, StateIngestor, TemporalSnapshot, TrafficOverlayResult, TwinConfidenceEvaluator, TwinModel, TwinReporter


def test_twin_reporter_keeps_state_distinctions_and_review_gate():
    ingestor = StateIngestor()
    logical = ingestor.ingest("edge-1", "logical", {"role": "core"}, source="design", evidence_ids=("d-1",), confidence=0.9)
    inferred = ingestor.ingest("edge-1", "inferred", {"state": "transition"}, source="estimator", evidence_ids=("i-1",), certainty="inferred", confidence=0.5)
    twin = TwinModel("twin-1", "2026-01-01").add_state(logical).add_state(inferred)
    confidence = TwinConfidenceEvaluator().evaluate(twin)
    drift = DriftEvent("drift-1", "2026-01-02", "edge-1", "version", "17.9", "17.6", "drift", "discovery", ("drift-e1",))
    overlay = TrafficOverlayResult("flow-1", "mismatch_observed", "denied", "allowed", "observed", "2026-01-02", ("flow-e1",), "mismatch")
    report = TwinReporter().report(twin, confidence, drift_events=[drift], traffic_overlay=[overlay])
    assert report.production_gate == "block_or_review"
    assert report.production_safe_claim_allowed is False
    assert report.state_views["logical_model"] == 1
    assert "inferred transient state exists" in " ".join(report.unverified_claims)
    assert report.drift_events[0].event_id == "drift-1"
    assert report.traffic_overlay[0].intent_id == "flow-1"
