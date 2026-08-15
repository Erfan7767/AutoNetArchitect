from deployment import ConnectionManager, ConnectionRequest, ConnectionState


def _request(vendor="cisco"):
    return ConnectionRequest("conn-1", "edge-1", vendor, "ios_xe", endpoint_reference="human://oob/edge-1", credential_reference="secret://conn/edge-1", evidence_ids=("conn-e1",))


def test_connection_manager_uses_driver_without_resolving_secret_values():
    received = []

    def driver(payload):
        received.append(payload)
        return {"state": "connected", "provider_reference": "session-1", "evidence_ids": ["session-e1"]}

    result = ConnectionManager(driver=driver).connect(_request())
    assert result.state == ConnectionState.CONNECTED.value
    assert result.production_path == "review_only"
    assert received[0]["credential_reference"] == "secret://conn/edge-1"


def test_connection_manager_blocks_preview_unknown_and_remote_destructive_paths():
    preview = ConnectionManager(preview_only_vendors=("vendor-preview",)).connect(_request("vendor-preview"))
    assert preview.state == ConnectionState.PREVIEW_ONLY.value
    unknown = ConnectionManager().connect(_request("unknown"))
    assert unknown.state == ConnectionState.BLOCKED_UNSUPPORTED_VENDOR.value
    blocked = ConnectionManager().connect(ConnectionRequest("conn-2", "edge-1", "cisco", "ios_xe", endpoint_reference="human://oob/edge-1", remote_destructive=True))
    assert blocked.state == ConnectionState.BLOCKED_REMOTE_DESTRUCTIVE.value
