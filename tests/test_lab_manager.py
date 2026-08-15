from lab import EveNgAdapter, GoldenStatus, LabConfig, LabManager, LabState, LabTopology


def _topology():
    return LabTopology("validation-lab", ({"name": "edge-1", "platform": "ios_xe", "template": "vios"},), ({"a": "edge-1", "b": "edge-2"},), design_ids=("decision-1",))


def test_lab_manager_deploys_and_pushes_only_through_validation_boundary():
    manager = LabManager([EveNgAdapter()])
    deployed = manager.deploy_topology("eve-ng", _topology())
    assert deployed.state == LabState.PREVIEW_ONLY.value
    assert deployed.validation_only is True
    assert deployed.production_change_control_required is True
    pushed = manager.push_configs("eve-ng", [LabConfig("edge-1", "cisco", "ios_xe", "hostname edge-1", artifact_id="cfg-1")])
    assert pushed[0].state == LabState.PREVIEW_ONLY.value
    blocked = manager.push_configs("eve-ng", [{"device_id": "edge-1", "rendered_config": "password: inline-secret"}])
    assert blocked[0].state == LabState.BLOCKED_MISSING_HUMAN_DATA.value


def test_lab_manager_compares_golden_outputs_without_treating_missing_evidence_as_match():
    matched = LabManager.compare_golden({"reachability": "verified", "routes": ["10.0.0.0/8"]}, {"reachability": "verified", "routes": ["10.0.0.0/8"]})
    assert matched.status == GoldenStatus.MATCHED.value
    mismatch = LabManager.compare_golden({"reachability": "failed"}, {"reachability": "verified"})
    assert mismatch.status == GoldenStatus.MISMATCH.value
    unknown = LabManager.compare_golden(None, {"reachability": "verified"})
    assert unknown.status == GoldenStatus.NOT_VERIFIABLE.value
