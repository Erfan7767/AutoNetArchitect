from datetime import datetime, timezone

from operations import HealthCheckDefinition, HealthChecker, HealthStatus, MonitoringObservation, MonitoringSnapshot


def _snapshot(values, state="observed"):
    now = datetime.now(timezone.utc).isoformat()
    observation = MonitoringObservation("CYCLE:T-1", "T-1", now, state, values, ("ev-health",))
    return MonitoringSnapshot("CYCLE", now, (observation,), True, ("ev-cycle",))


def test_health_checker_returns_healthy_for_matching_expectations():
    report = HealthChecker().evaluate("HEALTH-1", _snapshot({"routing": {"state": "up"}, "ntp": "synchronized"}), (HealthCheckDefinition("CHK-1", "T-1", "routing.state", "up", "high"), HealthCheckDefinition("CHK-2", "T-1", "ntp", "synchronized", "medium")))
    assert report.status == HealthStatus.HEALTHY.value
    assert report.production_gate == "allow"
    assert all(item.status == HealthStatus.HEALTHY.value for item in report.results)


def test_health_checker_returns_degraded_or_unhealthy_for_mismatches():
    degraded = HealthChecker().evaluate("HEALTH-2", _snapshot({"routing": {"state": "down"}}), (HealthCheckDefinition("CHK-1", "T-1", "routing.state", "up", "medium"),))
    assert degraded.status == HealthStatus.DEGRADED.value
    assert degraded.production_gate == "review_only"
    unhealthy = HealthChecker().evaluate("HEALTH-3", _snapshot({"routing": {"state": "down"}}), (HealthCheckDefinition("CHK-1", "T-1", "routing.state", "up", "critical"),))
    assert unhealthy.status == HealthStatus.UNHEALTHY.value
    assert unhealthy.production_gate == "block_or_review"


def test_health_checker_marks_missing_observation_as_unknown_and_never_remediates():
    report = HealthChecker().evaluate("HEALTH-4", _snapshot({}, state="failed"), (HealthCheckDefinition("CHK-1", "T-1", "routing.state", "up"),))
    assert report.status == HealthStatus.UNKNOWN.value
    assert report.production_gate == "block_or_review"
    assert report.read_only is True
