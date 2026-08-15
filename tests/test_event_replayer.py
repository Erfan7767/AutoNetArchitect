from digital_twin import EventReplayer, StateIngestor, StateCertainty, TwinEvent


def test_event_replayer_reconstructs_historical_state_with_replayed_provenance():
    base = StateIngestor().ingest("edge-1", "operational", {"state": "up", "version": "17.9"}, source="nms", evidence_ids=("base-1",), observed_at="2026-01-01T00:00:00Z", confidence=0.8)
    result = EventReplayer().replay({"edge-1": base}, [TwinEvent("evt-1", "2026-01-02T00:00:00Z", "edge-1", "state_update", {"state": "down"}, ("evt-e1",))], as_of="2026-01-03T00:00:00Z")
    assert result.status == "replayed"
    assert result.applied_event_ids == ("evt-1",)
    assert result.states[0].kind == "replayed_historical_state"
    assert result.states[0].provenance.certainty == StateCertainty.REPLAYED.value
    assert result.states[0].values["state"] == "down"


def test_event_replayer_marks_unknown_event_as_skipped():
    base = StateIngestor().ingest("edge-1", "operational", {"state": "up"}, source="nms", confidence=0.8)
    result = EventReplayer().replay({"edge-1": base}, [{"event_id": "evt-x", "timestamp": "2026-01-02", "entity_id": "edge-1", "event_type": "vendor_transition", "payload": {}}])
    assert result.skipped_event_ids == ("evt-x",)
    assert result.status == "not_verifiable_with_current_inputs"
