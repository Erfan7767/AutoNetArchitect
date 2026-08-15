from digital_twin import FailureInjectionRequest, FailureInjector, StateIngestor, TwinModel


def _twin():
    state = StateIngestor().ingest("edge-1", "operational", {"state": "up"}, source="nms", evidence_ids=("op-1",), confidence=0.8)
    return TwinModel("twin-1", "2026-01-01").add_state(state)


def test_failure_injection_returns_isolated_projection_only():
    twin = _twin()
    result = FailureInjector().inject(twin, FailureInjectionRequest("inj-1", "edge-1", "power_loss", "analyze single device loss", evidence_ids=("scenario-1",)))
    assert result.status == "projected"
    assert result.production_execution_allowed is False
    assert result.injected_state.kind == "inferred_transient_state"
    assert twin.latest("edge-1").values["state"] == "up"
    assert result.projected_twin.latest("edge-1").values["state"] == "failed"


def test_failure_injection_blocks_unsafe_request_and_unknown_entity():
    unsafe = FailureInjector().inject(_twin(), FailureInjectionRequest("inj-2", "edge-1", "link_loss", "unsafe", analysis_only=False))
    assert unsafe.status == "blocked_unsafe_mode"
    unknown = FailureInjector().inject(_twin(), FailureInjectionRequest("inj-3", "missing", "link_loss", "analysis"))
    assert unknown.status == "unknown_entity"
