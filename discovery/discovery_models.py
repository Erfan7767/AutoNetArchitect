"""Shared immutable models for safe discovery and vendor profiling."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DiscoveryStatus(str, Enum):
    """Lifecycle outcomes for a discovery operation."""

    COLLECTED = "collected"
    PARTIAL = "partial"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_UNSAFE_MODE = "blocked_unsafe_mode"
    UNSUPPORTED_VENDOR = "unsupported_vendor"
    UNKNOWN_DEVICE = "unknown_device"
    ERROR = "error"


class ConfidenceLevel(str, Enum):
    """Conservative confidence labels used by parsers and profilers."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class ReconciliationStatus(str, Enum):
    """Outcomes for comparing lifecycle asset records."""

    ALIGNED = "aligned"
    DRIFT = "drift"
    MISSING_FROM_DISCOVERED = "missing_from_discovered"
    UNEXPECTED_DISCOVERED = "unexpected_discovered"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class DiscoveryRequest:
    """Human-scoped request for a read-only discovery collection."""

    device_id: str
    vendor: str
    platform: str = ""
    model: str = ""
    commands: tuple[str, ...] = ()
    read_only: bool = True
    consent: bool = False
    source: str = "human_supplied"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible request representation."""
        return asdict(self)


@dataclass(frozen=True)
class DiscoverySnapshot:
    """Sanitized read-only command output with deterministic evidence hash."""

    device_id: str
    vendor: str
    platform: str
    model: str
    source: str
    acquired_at: str
    raw_outputs: dict[str, str]
    read_only: bool
    sanitized: bool
    evidence_hash: str
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the snapshot without exposing unsanitized secrets."""
        return asdict(self) | {"errors": list(self.errors)}


@dataclass(frozen=True)
class DiscoveryCollectionResult:
    """Outcome of a discovery request and its evidence snapshot."""

    status: str
    request: DiscoveryRequest
    snapshot: DiscoverySnapshot | None
    required_human_inputs: tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the collection result."""
        return {
            "status": self.status,
            "request": self.request.to_dict(),
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "required_human_inputs": list(self.required_human_inputs),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ParsedDevice:
    """Vendor parser output before governance and profiling decisions."""

    parser_name: str
    vendor: str
    platform: str
    model: str
    version: str
    serial: str
    hostname: str
    observations: dict[str, Any] = field(default_factory=dict)
    confidence: str = ConfidenceLevel.UNKNOWN.value
    ambiguous_fields: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()
    evidence_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize parser output and its uncertainty markers."""
        return asdict(self) | {
            "ambiguous_fields": list(self.ambiguous_fields),
            "unsupported_features": list(self.unsupported_features),
        }


@dataclass(frozen=True)
class DeviceProfile:
    """Governed device profile suitable for reconciliation inputs."""

    device_id: str
    vendor: str
    platform: str
    model: str
    version: str
    serial: str
    hostname: str
    parser_name: str
    status: str
    confidence: str
    safe_for_production: bool
    observations: dict[str, Any] = field(default_factory=dict)
    ambiguous_fields: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()
    missing_inputs: tuple[str, ...] = ()
    evidence_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize a profile without turning uncertainty into facts."""
        return asdict(self) | {
            "ambiguous_fields": list(self.ambiguous_fields),
            "unsupported_features": list(self.unsupported_features),
            "missing_inputs": list(self.missing_inputs),
        }
