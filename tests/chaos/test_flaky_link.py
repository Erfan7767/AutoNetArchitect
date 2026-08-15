"""Chaos test for a flaky connection driver."""
from __future__ import annotations

from deployment.connection_manager import ConnectionManager, ConnectionRequest, ConnectionState


def test_flaky_link_failure_is_recorded_without_implicit_retry():
    calls: list[int] = []

    def flaky_driver(_payload):
        calls.append(1)
        return {"state": "failed", "reasons": ["link flapped during read-only collection"]}

    manager = ConnectionManager(driver=flaky_driver)
    request = ConnectionRequest(connection_id="FLAKY-001", device_id="DEVICE-FLAKY", vendor="cisco", platform="ios-xe", endpoint_reference="oob://flaky", credential_reference="secret://cred", read_only=True, evidence_ids=("LINK-EVID-001",))
    result = manager.connect(request)
    assert result.state == ConnectionState.FAILED.value
    assert calls == [1]
    assert result.production_path == "review_only"
    assert "link flapped" in result.reasons[0]
