from digital_twin import TopologyEvolution


def test_topology_evolution_tracks_versioned_changes():
    evolution = TopologyEvolution()
    first = evolution.record("2026-01-01", "logical_model", [{"id": "a", "role": "edge"}, {"id": "b", "role": "core"}], [{"id": "ab", "source": "a", "target": "b"}], ["topo-1"])
    second = evolution.record("2026-01-02", "discovered", [{"id": "a", "role": "edge"}, {"id": "b", "role": "distribution"}, {"id": "c", "role": "access"}], [{"id": "ab", "source": "a", "target": "b"}, {"id": "bc", "source": "b", "target": "c"}], ["topo-2"])
    assert first.version_id != second.version_id
    change = evolution.changes()[0]
    assert change.added_nodes == ("c",)
    assert change.changed_nodes == ("b",)
    assert change.added_links == ("bc",)
    assert change.evidence_ids == ("topo-1", "topo-2")
