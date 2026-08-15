from lab import Gns3Adapter, LabConfig, LabState, LabTopology


def test_gns3_adapter_supports_deploy_push_and_preview_verification():
    adapter = Gns3Adapter()
    topology = LabTopology("gns3-project", ({"name": "r1", "template": "iosv", "node_type": "router"},), ({"a": "r1", "b": "sw1"},))
    deployed = adapter.deploy_topology(topology)
    assert deployed.state == LabState.PREVIEW_ONLY.value
    pushed = adapter.push_config(LabConfig("r1", "cisco", "ios_xe", "hostname r1", artifact_id="cfg-gns3"))
    assert pushed.state == LabState.PREVIEW_ONLY.value
    execution = adapter.run_verification({"project_name": "gns3-project", "checks": ["interfaces"]})
    assert execution.operation.state == LabState.PREVIEW_ONLY.value
    assert execution.observations == {}
