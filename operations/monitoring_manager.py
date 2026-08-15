"""Read-only monitoring primitives for AutoNetArchitect operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from log_redaction.redacting_filter import RedactingFilter


ObservationCollector = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class MonitoringTarget:
    """Reference to a monitored device or service without credential values."""

    target_id: str
    device_id: str
    vendor: str = ""
    platform: str = ""
    model: str = ""
    endpoint_reference: str = ""
    credential_reference: str = ""
    site_id: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize reference-only monitoring target metadata."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class MonitoringObservation:
    """One sanitized read-only observation returned by a collector."""

    observation_id: str
    target_id: str
    observed_at: str
    state: str
    values: dict[str, Any]
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize an observation."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "reasons": list(self.reasons)}


@dataclass(frozen=True)
class MonitoringSnapshot:
    """Collection result for a read-only monitoring cycle."""

    cycle_id: str
    collected_at: str
    observations: tuple[MonitoringObservation, ...]
    read_only: bool
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete snapshot."""
        return {"cycle_id": self.cycle_id, "collected_at": self.collected_at, "observations": [item.to_dict() for item in self.observations], "read_only": self.read_only, "evidence_ids": list(self.evidence_ids), "reasons": list(self.reasons)}


class MonitoringManager:
    """Collect operational observations without configuration or remediation writes."""

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create a monitoring manager with optional audit integration."""
        self.audit_trail = audit_trail
        self._last_snapshot: MonitoringSnapshot | None = None

    def collect(self, cycle_id: str, targets: Sequence[MonitoringTarget], collector: ObservationCollector) -> MonitoringSnapshot:
        """Collect one read-only cycle through an explicitly supplied collector."""
        if not cycle_id:
            raise ValueError("cycle_id is required")
        if not targets:
            raise ValueError("at least one monitoring target is required")
        observations: list[MonitoringObservation] = []
        evidence: set[str] = set()
        collected_at = datetime.now(timezone.utc).isoformat()
        for target in targets:
            if target.credential_reference and not target.credential_reference.startswith("secret://"):
                observation = MonitoringObservation(f"{cycle_id}:{target.target_id}", target.target_id, collected_at, "blocked", {}, target.evidence_ids, ("credential_reference must be a secret:// reference",))
                observations.append(observation)
                continue
            payload = {"operation": "collect_evidence", "read_only": True, "target": target.to_dict()}
            try:
                response = dict(collector(payload))
                if bool(response.get("write_attempted", False)) or str(response.get("operation", "collect_evidence")).lower() not in {"collect_evidence", "discover", "verify", "health_check", "show"}:
                    observation = MonitoringObservation(f"{cycle_id}:{target.target_id}", target.target_id, collected_at, "blocked", {}, target.evidence_ids, ("collector attempted or declared a non-read-only operation",))
                else:
                    raw_values = response.get("values", response.get("output", {}))
                    sanitized_values = RedactingFilter.sanitize_value(raw_values)
                    values = sanitized_values if isinstance(sanitized_values, dict) else {"output": sanitized_values}
                    response_evidence = tuple(str(item) for item in response.get("evidence_ids", ()))
                    response_reasons = tuple(str(item) for item in response.get("reasons", ()))
                    state = str(response.get("state", response.get("status", "observed"))).lower()
                    observation = MonitoringObservation(f"{cycle_id}:{target.target_id}", target.target_id, collected_at, state, values, tuple(dict.fromkeys(target.evidence_ids + response_evidence)), response_reasons)
            except Exception:
                observation = MonitoringObservation(f"{cycle_id}:{target.target_id}", target.target_id, collected_at, "failed", {}, target.evidence_ids, ("collector failed without exposing runtime details",))
            observations.append(observation)
            evidence.update(observation.evidence_ids)
        snapshot = MonitoringSnapshot(cycle_id, collected_at, tuple(observations), True, tuple(sorted(evidence)))
        self._last_snapshot = snapshot
        self._audit(cycle_id, snapshot)
        return snapshot

    def last_snapshot(self) -> MonitoringSnapshot | None:
        """Return the most recently collected snapshot, if one exists."""
        return self._last_snapshot

    def _audit(self, cycle_id: str, snapshot: MonitoringSnapshot) -> None:
        """Record collection metadata without raw outputs or credentials."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("operations.monitoring", "monitoring_manager", {"cycle_id": cycle_id, "read_only": snapshot.read_only, "observation_count": len(snapshot.observations), "evidence_ids": list(snapshot.evidence_ids)}, outcome="success" if all(item.state not in {"failed", "blocked"} for item in snapshot.observations) else "partial")
