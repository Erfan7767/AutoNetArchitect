from digital_twin import OverlayStatus, TrafficIntentOverlay


def test_traffic_overlay_compares_observed_and_inferred_flow_states():
    intents = [
        {"intent_id": "flow-1", "source": "users", "destination": "dns", "expected": "allowed"},
        {"intent_id": "flow-2", "source": "guest", "destination": "admin", "expected": "denied"},
        {"intent_id": "flow-3", "source": "iot", "destination": "siem", "expected": "allowed"},
    ]
    observed = {
        "flow-1": {"state": "allowed", "certainty": "observed", "observed_at": "2026-01-02", "evidence_ids": ["flow-e1"]},
        "flow-2": {"state": "allowed", "certainty": "observed", "evidence_ids": ["flow-e2"]},
        "flow-3": {"state": "allowed", "certainty": "inferred", "evidence_ids": ["flow-e3"]},
    }
    results = {item.intent_id: item for item in TrafficIntentOverlay().compare(intents, observed)}
    assert results["flow-1"].status == OverlayStatus.MATCHED_OBSERVED.value
    assert results["flow-2"].status == OverlayStatus.MISMATCH_OBSERVED.value
    assert results["flow-3"].status == OverlayStatus.MATCHED_INFERRED.value


def test_traffic_overlay_marks_missing_observation_not_verifiable():
    result = TrafficIntentOverlay().compare([{ "intent_id": "flow-1", "source": "a", "destination": "b", "expected": "allowed" }], {})[0]
    assert result.status == OverlayStatus.NOT_VERIFIABLE.value
