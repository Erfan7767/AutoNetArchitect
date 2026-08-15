from troubleshooting.models import AffectedScope, AffectedScopeType
from troubleshooting.recent_change_correlator import RecentChangeCorrelator


def test_recent_change_correlator_finds_same_device_feature():
    scope = AffectedScope(scope_type=AffectedScopeType.DEVICE, identifiers=["r1"], site_id="s1")
    result = RecentChangeCorrelator().correlate(scope, [{"change_id":"c1", "affected_devices":["r1"], "feature_area":"routing", "changed_at":"2026-01-01T00:00:00+00:00"}], now=__import__("datetime").datetime.fromisoformat("2026-01-01T01:00:00+00:00"), feature_area="routing")
    assert result[0].correlation_strength == "high"


def test_recent_change_correlator_returns_empty_without_scope_relation():
    scope = AffectedScope(scope_type=AffectedScopeType.DEVICE, identifiers=["r1"])
    assert RecentChangeCorrelator().correlate(scope, [{"change_id":"c1", "affected_devices":["r2"]}]) == []
