from discovery import DeviceProfiler, DiscoveryRequest, NetworkDiscovery


def _snapshot(vendor: str, output: str, platform: str = ""):
    request = DiscoveryRequest(device_id="device-1", vendor=vendor, platform=platform, consent=True)
    result = NetworkDiscovery().collect(request, {"identity": output})
    assert result.snapshot is not None
    return result.snapshot


def test_device_profiler_marks_complete_supported_identity_high_confidence():
    snapshot = _snapshot("cisco", "hostname edge-1\nCisco IOS XE Software, Version 17.9.4\nModel number : C9300-24T\nProcessor board ID FDO123")
    profile = DeviceProfiler().profile(snapshot)
    assert profile.status == "collected"
    assert profile.confidence == "high"
    assert profile.safe_for_production is True
    assert profile.model == "C9300-24T"


def test_device_profiler_does_not_invent_unknown_or_unsupported_identity():
    unknown = DeviceProfiler().profile(_snapshot("cisco", "Cisco device output without identity"))
    assert unknown.status == "unknown_device"
    assert unknown.safe_for_production is False
    unsupported = DeviceProfiler().profile(_snapshot("unsupported-vendor", "model X version 1 serial Y"))
    assert unsupported.status == "unsupported_vendor"
    assert unsupported.confidence == "unknown"
    assert unsupported.safe_for_production is False
