from oob_management import OOBDesigner, OOBStatus


def test_oob_designer_builds_redundant_reviewable_paths_from_human_references():
    design = OOBDesigner().design("site-1", [
        {"device_id": "edge-1", "transport": "serial", "endpoint_reference": "human://console/edge-1", "primary": True, "authentication_reference": "secret://oob/edge-1"},
        {"device_id": "edge-1", "transport": "cellular", "endpoint_reference": "human://cellular/edge-1", "primary": False, "authentication_reference": "secret://oob/edge-1"},
    ], transport_scope=["serial", "cellular"], evidence_ids=["oob-e1"])
    assert design.status == OOBStatus.READY_FOR_REVIEW.value
    assert len(design.paths) == 2
    assert design.production_safe_claim_allowed is False
    assert all(path.endpoint_reference.startswith("human://") for path in design.paths)


def test_oob_designer_blocks_missing_endpoint_and_bad_auth_reference():
    blocked = OOBDesigner().design("site-1", [{"device_id": "edge-1", "transport": "serial"}], transport_scope=["serial"])
    assert blocked.status == OOBStatus.BLOCKED_MISSING_HUMAN_DATA.value
    bad_auth = OOBDesigner().design("site-1", [{"device_id": "edge-1", "transport": "serial", "endpoint_reference": "human://console/edge-1", "authentication_reference": "raw-value"}], transport_scope=["serial"], redundancy_required=False)
    assert bad_auth.status == OOBStatus.BLOCKED_MISSING_HUMAN_DATA.value
