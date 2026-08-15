from lab import ContainerlabAdapter, LabConfig, LabState, LabTopology


def test_containerlab_adapter_maps_topology_and_rejects_inline_secret():
    adapter = ContainerlabAdapter()
    topology = LabTopology("clab-lab", ({"name": "leaf-1", "kind": "ceos", "image": "ceos:latest"},))
    deployed = adapter.deploy_topology(topology)
    assert deployed.state == LabState.PREVIEW_ONLY.value
    safe = adapter.push_config(LabConfig("leaf-1", "arista", "eos", "hostname leaf-1", secret_references=("secret://lab/ssh",)))
    assert safe.state == LabState.PREVIEW_ONLY.value
    blocked = adapter.push_config(LabConfig("leaf-1", "arista", "eos", "password: inline-secret"))
    assert blocked.state == LabState.BLOCKED_MISSING_HUMAN_DATA.value
