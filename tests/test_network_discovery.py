from discovery import DiscoveryRequest, DiscoveryStatus, NetworkDiscovery


def test_network_discovery_blocks_without_consent_and_collects_sanitized_output():
    collector = NetworkDiscovery()
    request = DiscoveryRequest(device_id="edge-1", vendor="cisco", consent=False)
    assert collector.collect(request, {"show version": "password: secret-value"}).status == DiscoveryStatus.BLOCKED_MISSING_HUMAN_DATA.value
    approved = DiscoveryRequest(device_id="edge-1", vendor="cisco", consent=True)
    result = collector.collect(approved, {"show version": "hostname edge-1\npassword: secret-value"})
    assert result.status == DiscoveryStatus.COLLECTED.value
    assert result.snapshot is not None
    assert "secret-value" not in result.snapshot.raw_outputs["show version"]
    assert result.snapshot.read_only is True
    assert result.snapshot.sanitized is True


def test_network_discovery_rejects_non_read_only_request_and_unknown_parser():
    collector = NetworkDiscovery()
    unsafe = DiscoveryRequest(device_id="edge-1", vendor="cisco", read_only=False, consent=True)
    assert collector.collect(unsafe, {"show version": "text"}).status == DiscoveryStatus.BLOCKED_UNSAFE_MODE.value
    assert collector.parser_for("unknown-vendor") is None
