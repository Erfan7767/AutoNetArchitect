"""Evidence-gated equipment capability matrix."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CapabilityRecord:
    """One capability assertion scoped to vendor, platform, model, version, and license."""

    vendor: str
    platform: str
    model: str
    capability: str
    min_version: str | None = None
    max_version: str | None = None
    license_ids: tuple[str, ...] = ()
    support_state: str = "requires_evidence"
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    support_scope: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CapabilityResult:
    """Result of resolving one capability request."""

    supported: bool
    reason: str
    record: CapabilityRecord | None = None
    evidence_chain: tuple[str, ...] = ()
    confidence: float = 0.0


class CapabilityMatrix:
    """Resolve capability support without converting unverified data into facts."""

    def __init__(
        self,
        records: Iterable[CapabilityRecord] | None = None,
        evidence_records: dict[str, dict[str, Any]] | None = None,
        source_records: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.records: list[CapabilityRecord] = list(records or [])
        self.evidence_records = dict(evidence_records or {})
        self.source_records = dict(source_records or {})

    @classmethod
    def from_json(cls, path: str | Path) -> "CapabilityMatrix":
        """Load a capability matrix from a JSON document."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        records = [cls._record_from_mapping(item) for item in payload.get("capabilities", [])]
        evidence = {str(item.get("evidence_id", key)): item for key, item in enumerate(payload.get("evidence_records", []))} if isinstance(payload.get("evidence_records"), list) else payload.get("evidence_records", {})
        sources = {str(item.get("source_id", key)): item for key, item in enumerate(payload.get("source_records", []))} if isinstance(payload.get("source_records"), list) else payload.get("source_records", {})
        return cls(records, evidence, sources)

    @staticmethod
    def _record_from_mapping(item: dict[str, Any]) -> CapabilityRecord:
        return CapabilityRecord(
            vendor=str(item["vendor"]),
            platform=str(item["platform"]),
            model=str(item["model"]),
            capability=str(item["capability"]),
            min_version=item.get("min_version"),
            max_version=item.get("max_version"),
            license_ids=tuple(str(value) for value in item.get("license_ids", [])),
            support_state=str(item.get("support_state", "requires_evidence")),
            evidence_ids=tuple(str(value) for value in item.get("evidence_ids", [])),
            source_ids=tuple(str(value) for value in item.get("source_ids", [])),
            confidence=float(item.get("confidence", 0.0)),
            support_scope=str(item.get("support_scope", "")),
            notes=str(item.get("notes", "")),
        )

    def register(self, record: CapabilityRecord) -> None:
        """Register one scoped capability record."""
        if not 0.0 <= record.confidence <= 1.0:
            raise ValueError("capability confidence must be between zero and one")
        self.records.append(record)

    def list_records(self) -> list[CapabilityRecord]:
        """Return a copy of all capability records."""
        return list(self.records)

    @staticmethod
    def _version_tuple(value: str | None) -> tuple[int, ...] | None:
        if value is None or value == "":
            return None
        pieces: list[int] = []
        for part in value.replace("-", ".").split("."):
            digits = "".join(character for character in part if character.isdigit())
            pieces.append(int(digits) if digits else 0)
        return tuple(pieces)

    @classmethod
    def _version_in_range(cls, version: str | None, minimum: str | None, maximum: str | None) -> bool:
        requested = cls._version_tuple(version)
        lower = cls._version_tuple(minimum)
        upper = cls._version_tuple(maximum)
        if requested is None and (lower is not None or upper is not None):
            return False
        if requested is None:
            return True
        return not ((lower is not None and requested < lower) or (upper is not None and requested > upper))

    def _evidence_usable(self, evidence_id: str) -> bool:
        evidence = self.evidence_records.get(evidence_id)
        if not evidence or evidence.get("verification_state") != "verified":
            return False
        if bool(evidence.get("revoked", False)) or bool(evidence.get("expired", False)):
            return False
        source_id = evidence.get("source_id")
        source = self.source_records.get(str(source_id)) if source_id else None
        return source is None or bool(source.get("verified", False))

    def supports(
        self,
        vendor: str,
        platform: str,
        model: str,
        version: str | None,
        capability: str,
        license_id: str | None = None,
        require_verified_evidence: bool = True,
    ) -> CapabilityResult:
        """Resolve one capability and return its traceable evidence chain."""
        matches = [
            record for record in self.records
            if record.vendor.lower() == vendor.lower()
            and record.platform.lower() == platform.lower()
            and record.model.lower() == model.lower()
            and record.capability.lower() == capability.lower()
            and self._version_in_range(version, record.min_version, record.max_version)
        ]
        if not matches:
            return CapabilityResult(False, "no_scoped_capability_record")
        for record in matches:
            if record.support_state not in {"supported", "supported_with_license"}:
                continue
            if record.license_ids and (license_id is None or license_id not in record.license_ids):
                continue
            chain = tuple(record.evidence_ids)
            if require_verified_evidence and (not chain or not all(self._evidence_usable(item) for item in chain)):
                continue
            return CapabilityResult(True, "capability_supported_with_traceable_evidence", record, chain, record.confidence)
        if any(record.support_state in {"unsupported", "not_supported"} for record in matches):
            return CapabilityResult(False, "capability_explicitly_unsupported")
        if any(record.license_ids for record in matches) and license_id is None:
            return CapabilityResult(False, "required_license_missing")
        return CapabilityResult(False, "capability_evidence_missing_or_not_verified")

    def evidence_for(self, request: dict[str, Any]) -> list[str]:
        """Return evidence IDs only when a capability request resolves."""
        result = self.supports(str(request["vendor"]), str(request["platform"]), str(request["model"]), request.get("version"), str(request["capability"]), request.get("license_id"))
        return list(result.evidence_chain) if result.supported else []
