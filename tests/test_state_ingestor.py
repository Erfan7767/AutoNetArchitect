from digital_twin import StateCertainty, StateIngestor


def test_state_ingestor_sets_source_and_explicit_certainty_defaults():
    state = StateIngestor().ingest("edge-1", "operational", {"health": "up"}, source="nms", evidence_ids=("op-1",), observed_at="2026-01-01T00:00:00Z", confidence=0.8)
    assert state.kind == "operational_state"
    assert state.provenance.certainty == StateCertainty.OBSERVED.value
    assert state.provenance.evidence_ids == ("op-1",)
    assert state.state_hash


def test_state_ingestor_rejects_unknown_kind_and_missing_source():
    rejected_kind = False
    try:
        StateIngestor().ingest("edge-1", "unsupported", {}, source="human")
    except ValueError:
        rejected_kind = True
    assert rejected_kind is True
    rejected_source = False
    try:
        StateIngestor().ingest("edge-1", "logical", {}, source="")
    except ValueError:
        rejected_source = True
    assert rejected_source is True
