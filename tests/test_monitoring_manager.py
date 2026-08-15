from operations import MonitoringManager, MonitoringTarget


def test_monitoring_manager_collects_read_only_observations():
    manager = MonitoringManager()
    target = MonitoringTarget("T-1", "edge-1", "cisco", "ios_xe", "C9300", "oob://edge-1", "secret://vault/edge-1", evidence_ids=("ev-target",))
    seen = []

    def collector(payload):
        seen.append(payload)
        return {"operation": "collect_evidence", "status": "observed", "values": {"routing": {"state": "up"}}, "evidence_ids": ["ev-observed"]}

    snapshot = manager.collect("CYCLE-1", (target,), collector)
    assert snapshot.read_only is True
    assert snapshot.observations[0].state == "observed"
    assert "ev-target" in snapshot.evidence_ids
    assert "ev-observed" in snapshot.evidence_ids
    assert seen[0]["read_only"] is True
    assert seen[0]["operation"] == "collect_evidence"


def test_monitoring_manager_blocks_write_attempts_and_bad_credential_references():
    manager = MonitoringManager()
    valid = MonitoringTarget("T-1", "edge-1", endpoint_reference="oob://edge-1", credential_reference="secret://vault/edge-1")
    bad = MonitoringTarget("T-2", "edge-2", endpoint_reference="oob://edge-2", credential_reference="raw-secret")
    snapshot = manager.collect("CYCLE-2", (valid, bad), lambda payload: {"write_attempted": True, "operation": "replace_config"})
    assert snapshot.observations[0].state == "blocked"
    assert snapshot.observations[1].state == "blocked"
    assert "collector attempted" in snapshot.observations[0].reasons[0]
    assert "secret://" in " ".join(snapshot.observations[1].reasons) or "credential_reference" in " ".join(snapshot.observations[1].reasons)
