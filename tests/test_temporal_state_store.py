from digital_twin import StateIngestor, TemporalStateStore


def test_temporal_state_store_keeps_versions_and_resolves_state_at_time():
    ingestor = StateIngestor()
    first = ingestor.ingest("edge-1", "operational", {"state": "up"}, source="nms", evidence_ids=("e1",), observed_at="2026-01-01T00:00:00Z", version=1, confidence=0.8)
    second = ingestor.ingest("edge-1", "operational", {"state": "down"}, source="nms", evidence_ids=("e2",), observed_at="2026-01-02T00:00:00Z", version=2, confidence=0.8)
    store = TemporalStateStore()
    store.append(first)
    store.append(second)
    assert store.at("edge-1", "2026-01-01T12:00:00Z").values["state"] == "up"
    assert store.at("edge-1", "2026-01-03T00:00:00Z").values["state"] == "down"
    snapshot = store.snapshot("snap-1", "2026-01-02T00:00:00Z", [second], replayed=True)
    assert snapshot.replayed is True
    assert store.state_count() == 2
