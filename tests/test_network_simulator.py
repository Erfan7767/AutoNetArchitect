from operations import NetworkSimulator, ResilienceStatus, SimulationStatus


def _topology():
    return {
        "nodes": [
            {"name": "a", "state": "up"},
            {"name": "b", "state": "up"},
            {"name": "c", "state": "up"},
            {"name": "d", "state": "up"},
        ],
        "links": [
            {"link_id": "ab", "source": "a", "target": "b", "state": "up"},
            {"link_id": "bd", "source": "b", "target": "d", "state": "up"},
            {"link_id": "ac", "source": "a", "target": "c", "state": "up"},
            {"link_id": "cd", "source": "c", "target": "d", "state": "up"},
        ],
    }


def test_network_simulator_is_logical_only_and_analyzes_surviving_path():
    simulator = NetworkSimulator()
    result = simulator.simulate(_topology(), {"a-d": {"source": "a", "destination": "d", "expected": "reachable"}}, events=[{"event_type": "disable_link", "target": "ab"}], resilience_scenarios=[{"scenario_id": "single-link", "event": {"event_type": "disable_link", "target": "ab"}}])
    assert result.status == SimulationStatus.COMPLETED.value
    assert result.path_results["a-d"] == "verified"
    assert result.simulator_kind == "logical_network_simulator"
    assert result.protocol_emulation is False
    assert result.production_claim_allowed is False
    assert result.resilience[0].status == ResilienceStatus.RESILIENT.value


def test_network_simulator_marks_unknown_events_and_missing_inputs_conservatively():
    unknown = NetworkSimulator().simulate(_topology(), {"a-d": {"source": "a", "destination": "d", "expected": "reachable"}}, events=[{"event_type": "unsupported_event", "target": "ab"}])
    assert unknown.status == SimulationStatus.NOT_VERIFIABLE.value
    blocked = NetworkSimulator().simulate(None, None)
    assert blocked.status == SimulationStatus.BLOCKED_MISSING_HUMAN_DATA.value
    assert blocked.production_claim_allowed is False
