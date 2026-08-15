"""Read-only operational health evaluation from monitoring observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Sequence

from .monitoring_manager import MonitoringSnapshot


class HealthStatus(str, Enum):
    """Health result taxonomy."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthCheckDefinition:
    """One explicit expected-value health check."""

    check_id: str
    target_id: str
    path: str
    expected: Any
    failure_severity: str = "medium"
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a health check definition."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of one observation-backed health check."""

    check_id: str
    target_id: str
    path: str
    expected: Any
    observed: Any
    status: str
    severity: str
    reason: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a health check result."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class HealthReport:
    """Aggregated operational health report."""

    report_id: str
    checked_at: str
    status: str
    read_only: bool
    results: tuple[HealthCheckResult, ...]
    production_gate: str
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report."""
        return {"report_id": self.report_id, "checked_at": self.checked_at, "status": self.status, "read_only": self.read_only, "results": [result.to_dict() for result in self.results], "production_gate": self.production_gate, "evidence_ids": list(self.evidence_ids), "reasons": list(self.reasons)}


class HealthChecker:
    """Evaluate explicit health criteria without auto-remediation."""

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create a checker with optional audit integration."""
        self.audit_trail = audit_trail

    def evaluate(self, report_id: str, snapshot: MonitoringSnapshot, definitions: Sequence[HealthCheckDefinition]) -> HealthReport:
        """Evaluate checks against one read-only monitoring snapshot."""
        if not report_id:
            raise ValueError("report_id is required")
        observation_map = {item.target_id: item for item in snapshot.observations}
        results: list[HealthCheckResult] = []
        evidence: set[str] = set(snapshot.evidence_ids)
        for definition in definitions:
            observation = observation_map.get(definition.target_id)
            if observation is None or observation.state in {"failed", "blocked"}:
                result = HealthCheckResult(definition.check_id, definition.target_id, definition.path, definition.expected, "<unknown>", HealthStatus.UNKNOWN.value, definition.failure_severity, "no usable observation exists for the target", definition.evidence_ids)
            else:
                observed_value = self._get_path(observation.values, definition.path)
                if observed_value is _MISSING:
                    result = HealthCheckResult(definition.check_id, definition.target_id, definition.path, definition.expected, "<missing>", HealthStatus.UNKNOWN.value, definition.failure_severity, "health path is absent from the observation", tuple(dict.fromkeys(definition.evidence_ids + observation.evidence_ids)))
                elif observed_value == definition.expected:
                    result = HealthCheckResult(definition.check_id, definition.target_id, definition.path, definition.expected, observed_value, HealthStatus.HEALTHY.value, "none", "observed value matches expected value", tuple(dict.fromkeys(definition.evidence_ids + observation.evidence_ids)))
                else:
                    status = HealthStatus.UNHEALTHY.value if definition.failure_severity.lower() in {"high", "critical"} else HealthStatus.DEGRADED.value
                    result = HealthCheckResult(definition.check_id, definition.target_id, definition.path, definition.expected, observed_value, status, definition.failure_severity, "observed value differs from the health expectation", tuple(dict.fromkeys(definition.evidence_ids + observation.evidence_ids)))
            results.append(result)
            evidence.update(result.evidence_ids)
        status = self._aggregate(results)
        gate = "allow" if status == HealthStatus.HEALTHY.value else "review_only" if status == HealthStatus.DEGRADED.value else "block_or_review"
        reasons = ("health is not fully verified; no remediation was attempted",) if status != HealthStatus.HEALTHY.value else ()
        report = HealthReport(report_id, snapshot.collected_at, status, True, tuple(results), gate, tuple(sorted(evidence)), reasons)
        self._audit(report)
        return report

    @staticmethod
    def _get_path(values: dict[str, Any], path: str) -> Any:
        """Read a dotted path from a mapping without coercing missing data."""
        current: Any = values
        for part in path.split(".") if path else ():
            if not isinstance(current, dict) or part not in current:
                return _MISSING
            current = current[part]
        return current

    @staticmethod
    def _aggregate(results: Sequence[HealthCheckResult]) -> str:
        """Aggregate individual results conservatively."""
        if not results:
            return HealthStatus.UNKNOWN.value
        statuses = {result.status for result in results}
        if HealthStatus.UNHEALTHY.value in statuses:
            return HealthStatus.UNHEALTHY.value
        if HealthStatus.DEGRADED.value in statuses:
            return HealthStatus.DEGRADED.value
        if HealthStatus.UNKNOWN.value in statuses:
            return HealthStatus.UNKNOWN.value
        return HealthStatus.HEALTHY.value

    def _audit(self, report: HealthReport) -> None:
        """Record health-check metadata without raw observation payloads."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("operations.health_check", "health_checker", {"report_id": report.report_id, "read_only": report.read_only, "status": report.status, "result_count": len(report.results), "production_gate": report.production_gate, "evidence_ids": list(report.evidence_ids)}, outcome=report.status)


_MISSING = object()
