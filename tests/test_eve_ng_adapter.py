from lab import EveNgAdapter, LabConfig, LabState, LabTopology


def _driver(operation, payload):
    if operation == "run_verification":
        return {"state": "executed", "observations": {"reachability": "verified"}, "raw_outputs": {"show": "password: hidden"}, "evidence_ids": ["eve-e1"], "provider_reference": "eve-job-1"}
    return {"state": "executed", "detail": operation + " completed", "provider_reference": "eve-job-1"}


def test_eve_ng_adapter_maps_payloads_and_sanitizes_verification_output():
    adapter = EveNgAdapter(_driver)
    topology = LabTopology("eve-lab", ({"name": "r1", "template": "vios", "image": "vios-image"},))
    deployed = adapter.deploy_topology(topology)
    assert deployed.state == LabState.EXECUTED.value
    pushed = adapter.push_config(LabConfig("r1", "cisco", "ios_xe", "hostname r1", artifact_id="cfg-1"))
    assert pushed.state == LabState.EXECUTED.value
    execution = adapter.run_verification({"topology_id": "eve-lab", "checks": ["reachability"]})
    assert execution.operation.state == LabState.EXECUTED.value
    assert execution.observations["reachability"] == "verified"
    assert "hidden" not in execution.raw_outputs["show"]
