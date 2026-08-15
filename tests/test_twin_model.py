from digital_twin import StateCertainty, StateIngestor, TwinModel


def test_twin_model_links_declared_and_observed_state_without_collapsing_provenance():
    ingestor = StateIngestor()
    logical = ingestor.ingest("edge-1", "logical", {"version": "17.9", "role": "core"}, source="design", evidence_ids=("design-1",), confidence=0.9)
    discovered = ingestor.ingest("edge-1", "discovered", {"version": "17.6", "role": "core"}, source="discovery", evidence_ids=("disc-1",), observed_at="2026-01-01T00:00:00Z", confidence=0.85)
    twin = TwinModel("twin-1", "2026-01-01T00:00:00Z").add_state(logical).add_state(discovered)
    assert twin.latest("edge-1", logical.kind).provenance.certainty == StateCertainty.DECLARED.value
    assert twin.latest("edge-1", discovered.kind).provenance.certainty == StateCertainty.OBSERVED.value
    assert set(twin.state_kinds()) == {"logical_model", "discovered_operational_state"}
    assert twin.full_fidelity_claim is False
