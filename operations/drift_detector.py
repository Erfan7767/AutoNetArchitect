"""Observation-driven drift detection against an authoritative OPERATIONAL_SOT."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping

from source_of_truth.sot_manager import SoTRecord, SoTType

from .monitoring_manager import MonitoringSnapshot


class DriftSeverity(str, Enum):
    """Operational drift severity."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DriftItem:
    """One expected-versus-observed difference."""

    target_id: str
    path: str
    expected: Any
    observed: Any
    severity: str
    status: str
    reason: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize one drift item."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class DriftReport:
    """Conservative drift report with explicit SoT and remediation gates."""

    report_id: str
    operational_sot_record_id: str
    operational_sot_version: int
    compared_at: str
    read_only: bool
    items: tuple[DriftItem, ...]
    severity: str
    production_gate: str
    remediation_allowed: bool
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report."""
        return {"report_id": self.report_id, "operational_sot_record_id": self.operational_sot_record_id, "operational_sot_version": self.operational_sot_version, "compared_at": self.compared_at, "read_only": self.read_only, "items": [item.to_dict() for item in self.items], "severity": self.severity, "production_gate": self.production_gate, "remediation_allowed": self.remediation_allowed, "reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}


class DriftDetector:
    """Detect drift without changing the network or automatically remediating it."""

    HIGH_RISK_PATHS = ("routing", "security", "acl", "management", "authentication", "segmentation", "firmware", "boot", "redundancy")

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create a detector with optional audit integration."""
        self.audit_trail = audit_trail

    def compare(self, report_id: str, observed: MonitoringSnapshot | Mapping[str, Any], operational_sot: SoTRecord) -> DriftReport:
        """Compare observed state with exactly one approved OPERATIONAL_SOT record."""
        if not report_id:
            raise ValueError("report_id is required")
        if not isinstance(operational_sot, SoTRecord) or operational_sot.sot_type != SoTType.OPERATIONAL.value or not operational_sot.approved:
            raise ValueError("drift detection requires one approved OPERATIONAL_SOT record")
        expected_by_target = self._expected_by_target(operational_sot.payload)
        observed_by_target, evidence = self._observed_by_target(observed)
        items: list[DriftItem] = []
        target_ids = sorted(set(expected_by_target) | set(observed_by_target))
        if not target_ids:
            items.append(DriftItem("", "", None, None, DriftSeverity.UNKNOWN.value, "not_verifiable", "OPERATIONAL_SOT and observation set contain no comparable target state", tuple(sorted(evidence))))
        for target_id in target_ids:
            expected = expected_by_target.get(target_id, {})
            actual = observed_by_target.get(target_id, {})
            expected_flat = self._flatten(expected)
            actual_flat = self._flatten(actual)
            for path in sorted(set(expected_flat) | set(actual_flat)):
                expected_value = expected_flat.get(path, "<missing>")
                observed_value = actual_flat.get(path, "<missing>")
                if expected_value == observed_value:
                    continue
                severity = self._severity_for(path, expected_value, observed_value)
                status = "missing_observation" if observed_value == "<missing>" else "drifted" if expected_value != "<missing>" else "unexpected_observation"
                reason = "observation is missing" if status == "missing_observation" else "observed value differs from OPERATIONAL_SOT" if status == "drifted" else "observed field is not present in OPERATIONAL_SOT"
                items.append(DriftItem(target_id, path, expected_value, observed_value, severity, status, reason, tuple(sorted(evidence))))
        severity = self._aggregate_severity(items)
        production_gate = "allow" if severity == DriftSeverity.NONE.value else "review_only" if severity in {DriftSeverity.LOW.value, DriftSeverity.MEDIUM.value} else "block_or_review"
        reasons = ("high-risk production drift requires explicit approval before any remediation",) if severity in {DriftSeverity.HIGH.value, DriftSeverity.CRITICAL.value} else ()
        report = DriftReport(report_id, operational_sot.record_id, operational_sot.version, self._timestamp(), True, tuple(items), severity, production_gate, False, reasons, tuple(sorted(evidence)))
        self._audit(report)
        return report

    @staticmethod
    def _expected_by_target(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        """Extract target-scoped expected state without interpreting unknown schemas."""
        candidate = payload.get("operational_state", payload.get("state", payload))
        if not isinstance(candidate, Mapping):
            return {}
        targets = candidate.get("targets")
        if isinstance(targets, Mapping):
            return {str(key): value for key, value in targets.items() if isinstance(value, Mapping)}
        if all(isinstance(value, Mapping) for value in candidate.values()):
            return {str(key): value for key, value in candidate.items()}
        return {"__global__": candidate}

    @staticmethod
    def _observed_by_target(observed: MonitoringSnapshot | Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
        """Normalize monitoring observations while preserving evidence IDs."""
        evidence: set[str] = set()
        if isinstance(observed, MonitoringSnapshot):
            result: dict[str, Mapping[str, Any]] = {}
            for item in observed.observations:
                result[item.target_id] = item.values
                evidence.update(item.evidence_ids)
            evidence.update(observed.evidence_ids)
            return result, evidence
        result = {}
        if isinstance(observed, Mapping):
            for key, value in observed.items():
                if key == "evidence_ids" and isinstance(value, (list, tuple, set)):
                    evidence.update(str(item) for item in value)
                elif isinstance(value, Mapping):
                    result[str(key)] = value
            return result, evidence
        return result, evidence

    @classmethod
    def _severity_for(cls, path: str, expected: Any, observed: Any) -> str:
        """Classify drift based on explicit path sensitivity, not business guesses."""
        lowered = path.lower()
        if any(token in lowered for token in cls.HIGH_RISK_PATHS):
            return DriftSeverity.HIGH.value
        if expected == "<missing>" or observed == "<missing>":
            return DriftSeverity.MEDIUM.value
        return DriftSeverity.LOW.value

    @staticmethod
    def _aggregate_severity(items: list[DriftItem]) -> str:
        """Return the highest severity represented by the report."""
        order = {DriftSeverity.NONE.value: 0, DriftSeverity.LOW.value: 1, DriftSeverity.MEDIUM.value: 2, DriftSeverity.HIGH.value: 3, DriftSeverity.CRITICAL.value: 4, DriftSeverity.UNKNOWN.value: 5}
        return max((item.severity for item in items), key=lambda value: order.get(value, 5), default=DriftSeverity.NONE.value)

    @staticmethod
    def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten nested mappings for deterministic field comparisons."""
        result: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(item, Mapping):
                result.update(DriftDetector._flatten(item, path))
            else:
                result[path] = item
        return result

    @staticmethod
    def _timestamp() -> str:
        """Return an RFC3339 UTC timestamp."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def _audit(self, report: DriftReport) -> None:
        """Record drift metadata without changing state."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("operations.drift_detection", "drift_detector", {"report_id": report.report_id, "operational_sot_record_id": report.operational_sot_record_id, "operational_sot_version": report.operational_sot_version, "read_only": report.read_only, "severity": report.severity, "item_count": len(report.items), "production_gate": report.production_gate, "evidence_ids": list(report.evidence_ids)}, outcome=report.severity)
