"""Safe vendor connection foundations for V1 deployment workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Mapping


class ConnectionState(str, Enum):
    """Connection lifecycle outcomes."""

    CONNECTED = "connected"
    PREVIEW_ONLY = "preview_only"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_UNSUPPORTED_VENDOR = "blocked_unsupported_vendor"
    BLOCKED_REMOTE_DESTRUCTIVE = "blocked_remote_destructive"
    FAILED = "failed"


@dataclass(frozen=True)
class ConnectionRequest:
    """Human-scoped connection request containing references, never secret values."""

    connection_id: str
    device_id: str
    vendor: str
    platform: str
    endpoint_reference: str = ""
    oob_reference: str = ""
    credential_reference: str = ""
    read_only: bool = True
    remote_destructive: bool = False
    production_requested: bool = False
    human_approval: bool = False
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request without secret resolution."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class ConnectionResult:
    """Auditable connection result with production boundary metadata."""

    connection_id: str
    state: str
    vendor: str
    device_id: str
    read_only: bool
    production_path: str
    provider_reference: str = ""
    required_human_inputs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result."""
        return asdict(self) | {"required_human_inputs": list(self.required_human_inputs), "reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}


ConnectionDriver = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class ConnectionManager:
    """Manage supported V1 vendor connections without hidden credentials or unsafe writes."""

    SUPPORTED_VENDORS = ("aruba", "cisco", "fortinet", "huawei", "juniper", "mikrotik", "paloalto")

    def __init__(self, driver: ConnectionDriver | None = None, preview_only_vendors: Iterable[str] = ()) -> None:
        """Create a manager with an optional externally controlled connection driver."""
        self.driver = driver
        self._preview_only = {str(item).strip().lower() for item in preview_only_vendors if str(item).strip()}

    def connect(self, request: ConnectionRequest) -> ConnectionResult:
        """Evaluate and optionally invoke a driver for one supported vendor connection."""
        evidence = tuple(dict.fromkeys(str(item) for item in request.evidence_ids))
        if request.remote_destructive:
            return ConnectionResult(request.connection_id, ConnectionState.BLOCKED_REMOTE_DESTRUCTIVE.value, request.vendor, request.device_id, request.read_only, "blocked", reasons=("remote-destructive connection path is blocked by policy",), evidence_ids=evidence)
        vendor = str(request.vendor).strip().lower()
        if vendor in self._preview_only:
            return ConnectionResult(request.connection_id, ConnectionState.PREVIEW_ONLY.value, request.vendor, request.device_id, True, "preview_only", required_human_inputs=("validated_vendor_connection_driver",), reasons=("vendor is explicitly preview-only and cannot enter production deployment path",), evidence_ids=evidence)
        if vendor not in self.SUPPORTED_VENDORS:
            return ConnectionResult(request.connection_id, ConnectionState.BLOCKED_UNSUPPORTED_VENDOR.value, request.vendor, request.device_id, request.read_only, "blocked", required_human_inputs=("supported_vendor_connection",), reasons=("vendor is not in the validated V1 connection set",), evidence_ids=evidence)
        missing = [field for field in ("connection_id", "device_id", "vendor", "platform") if not getattr(request, field)]
        if not request.endpoint_reference and not request.oob_reference:
            missing.append("endpoint_reference_or_oob_reference")
        if request.credential_reference and not request.credential_reference.startswith("secret://"):
            missing.append("credential_reference_must_be_secret_reference")
        if missing:
            return ConnectionResult(request.connection_id, ConnectionState.BLOCKED_MISSING_HUMAN_DATA.value, request.vendor, request.device_id, request.read_only, "blocked", required_human_inputs=tuple(dict.fromkeys(missing)), reasons=("connection inputs are incomplete",), evidence_ids=evidence)
        if request.production_requested and not request.human_approval:
            return ConnectionResult(request.connection_id, ConnectionState.BLOCKED_MISSING_HUMAN_DATA.value, request.vendor, request.device_id, request.read_only, "blocked", required_human_inputs=("human_change_approval",), reasons=("production connection request lacks explicit human approval",), evidence_ids=evidence)
        if self.driver is None:
            return ConnectionResult(request.connection_id, ConnectionState.PREVIEW_ONLY.value, request.vendor, request.device_id, True, "preview_only", required_human_inputs=("connection_driver",), reasons=("no connection driver is configured; no session was opened",), evidence_ids=evidence)
        try:
            result = dict(self.driver(request.to_dict()))
        except Exception:
            return ConnectionResult(request.connection_id, ConnectionState.FAILED.value, request.vendor, request.device_id, request.read_only, "blocked", reasons=("connection driver failed without exposing runtime details",), evidence_ids=evidence)
        state = ConnectionState.CONNECTED.value if str(result.get("state", "")) == ConnectionState.CONNECTED.value else ConnectionState.FAILED.value
        return ConnectionResult(request.connection_id, state, request.vendor, request.device_id, request.read_only, "requires_change_control" if request.production_requested else "review_only", str(result.get("provider_reference", "")), tuple(str(item) for item in result.get("required_human_inputs", ())), tuple(str(item) for item in result.get("reasons", ())), tuple(dict.fromkeys(evidence + tuple(str(item) for item in result.get("evidence_ids", ())))))

    def supported_vendors(self) -> tuple[str, ...]:
        """Return validated V1 vendors."""
        return tuple(sorted(self.SUPPORTED_VENDORS))

    def preview_only_vendors(self) -> tuple[str, ...]:
        """Return explicitly preview-only vendors."""
        return tuple(sorted(self._preview_only))
