from digital_twin import DriftTimeline, StateIngestor


def test_drift_timeline_records_temporal_differences_with_evidence():
    ingestor = StateIngestor()
    expected = ingestor.ingest("edge-1", "logical", {"version": "17.9", "role": "core"}, source="design", evidence_ids=("d-1",), confidence=0.9)
    observed = ingestor.ingest("edge-1", "discovered", {"version": "17.6", "role": "core"}, source="discovery", evidence_ids=("o-1",), observed_at="2026-01-02", confidence=0.8)
    timeline = DriftTimeline()
    events = timeline.compare(expected, observed)
    assert len(events) == 1
    assert events[0].field == "version"
    assert events[0].evidence_ids == ("d-1", "o-1")
    assert timeline.summary()["drift"] == 1
