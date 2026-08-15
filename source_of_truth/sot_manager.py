"""Source of Truth manager with explicit authority and conflict enforcement."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any
import uuid


class SoTType(str, Enum):
    """Supported source-of-truth domains."""

    DESIGN = "DESIGN"
    DEPLOYMENT = "DEPLOYMENT"
    OPERATIONAL = "OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"


class SoTError(RuntimeError):
    """Base source-of-truth error."""


class SoTConflictError(SoTError):
    """Raised when multiple approved records compete for authority."""


class SoTNotFoundError(SoTError):
    """Raised when a required source of truth is unavailable."""


@dataclass(frozen=True)
class SoTRecord:
    """Versioned, checksum-protected source-of-truth record."""

    record_id: str
    sot_type: str
    version: int
    payload: dict[str, Any]
    authority: str
    source: str
    evidence_ids: tuple[str, ...]
    approved: bool
    created_at: str
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize a record deterministically."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


class SoTManager:
    """Persist and resolve authoritative records for four governed domains."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: dict[str, SoTRecord] = {}
        self._load()
        self.verify_integrity()

    def register(self, sot_type: SoTType | str, payload: dict[str, Any], authority: str, source: str, evidence_ids: tuple[str, ...] = (), approved: bool = False, record_id: str | None = None) -> SoTRecord:
        """Register one immutable versioned record."""
        normalized = self._normalize_type(sot_type)
        if not isinstance(payload, dict) or not payload:
            raise ValueError("SoT payload must be a non-empty dictionary")
        if not authority or not source:
            raise ValueError("authority and source are required")
        previous = [record for record in self._records.values() if record.sot_type == normalized]
        version = max((record.version for record in previous), default=0) + 1
        created_at = datetime.now(timezone.utc).isoformat()
        identifier = record_id or f"sot:{normalized.lower()}:{uuid.uuid4()}"
        unsigned = {"record_id": identifier, "sot_type": normalized, "version": version, "payload": payload, "authority": authority, "source": source, "evidence_ids": list(evidence_ids), "approved": approved, "created_at": created_at}
        record = SoTRecord(identifier, normalized, version, dict(payload), authority, source, tuple(evidence_ids), approved, created_at, self._checksum(unsigned))
        self._records[identifier] = record
        self._persist()
        return record

    def approve(self, record_id: str, authority: str | None = None) -> SoTRecord:
        """Approve one record; conflicts are detected during resolution."""
        record = self.get(record_id)
        updated = SoTRecord(record.record_id, record.sot_type, record.version, record.payload, authority or record.authority, record.source, record.evidence_ids, True, record.created_at, "")
        updated = self._with_checksum(updated)
        self._records[record_id] = updated
        self._persist()
        return updated

    def get(self, record_id: str) -> SoTRecord:
        """Return one record by ID."""
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise SoTNotFoundError(f"SoT record not found: {record_id}") from exc

    def list(self, sot_type: SoTType | str | None = None, approved_only: bool = False) -> tuple[SoTRecord, ...]:
        """List records deterministically with optional domain/status filters."""
        normalized = self._normalize_type(sot_type) if sot_type is not None else None
        records = [record for record in self._records.values() if (normalized is None or record.sot_type == normalized) and (not approved_only or record.approved)]
        return tuple(sorted(records, key=lambda record: (record.sot_type, record.version, record.record_id)))

    def authoritative(self, sot_type: SoTType | str, record_id: str | None = None) -> SoTRecord:
        """Resolve exactly one approved authoritative record or block on conflict."""
        normalized = self._normalize_type(sot_type)
        if record_id is not None:
            record = self.get(record_id)
            if record.sot_type != normalized or not record.approved:
                raise SoTConflictError("selected record is not an approved record for the requested SoT type")
            return record
        approved = self.list(normalized, approved_only=True)
        if not approved:
            raise SoTNotFoundError(f"no approved SoT record for {normalized}")
        if len(approved) > 1:
            raise SoTConflictError(f"multiple approved SoT records exist for {normalized}")
        return approved[0]

    def require(self, required_types: tuple[SoTType | str, ...]) -> dict[str, SoTRecord]:
        """Resolve all required types and block if any is missing or conflicting."""
        result: dict[str, SoTRecord] = {}
        for sot_type in required_types:
            normalized = self._normalize_type(sot_type)
            result[normalized] = self.authoritative(normalized)
        return result

    def verify_integrity(self) -> bool:
        """Verify every record checksum."""
        for record in self._records.values():
            if record.checksum != self._checksum({"record_id": record.record_id, "sot_type": record.sot_type, "version": record.version, "payload": record.payload, "authority": record.authority, "source": record.source, "evidence_ids": list(record.evidence_ids), "approved": record.approved, "created_at": record.created_at}):
                raise SoTError(f"SoT checksum mismatch: {record.record_id}")
        return True

    def _with_checksum(self, record: SoTRecord) -> SoTRecord:
        checksum = self._checksum({"record_id": record.record_id, "sot_type": record.sot_type, "version": record.version, "payload": record.payload, "authority": record.authority, "source": record.source, "evidence_ids": list(record.evidence_ids), "approved": record.approved, "created_at": record.created_at})
        return SoTRecord(record.record_id, record.sot_type, record.version, record.payload, record.authority, record.source, record.evidence_ids, record.approved, record.created_at, checksum)

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SoTError("SoT store must be a JSON object")
        self._records = {record_id: SoTRecord(record_id, str(item["sot_type"]), int(item["version"]), dict(item["payload"]), str(item["authority"]), str(item["source"]), tuple(str(value) for value in item.get("evidence_ids", [])), bool(item.get("approved", False)), str(item["created_at"]), str(item["checksum"])) for record_id, item in payload.items()}

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {record_id: record.to_dict() for record_id, record in sorted(self._records.items())}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _normalize_type(sot_type: SoTType | str | None) -> str:
        if isinstance(sot_type, SoTType):
            return sot_type.value
        if isinstance(sot_type, str):
            value = sot_type.upper()
            if value in {item.value for item in SoTType}:
                return value
        raise ValueError("sot_type must be DESIGN, DEPLOYMENT, OPERATIONAL, or COMPLIANCE")

    @staticmethod
    def _checksum(unsigned: dict[str, Any]) -> str:
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
