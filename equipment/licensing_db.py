"""Licensing requirements and evidence-aware feature entitlement lookup."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class LicenseRecord:
    """One license tier and the capabilities it is allowed to activate."""

    vendor: str
    license_id: str
    tier: str
    feature_set: tuple[str, ...] = ()
    production_eligible: bool = False
    verification_state: str = "requires_evidence"
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    support_scope: str = ""
    term_months: int | None = None
    confidence: float = 0.0


class LicensingDB:
    """Resolve licenses while keeping entitlement claims evidence-gated."""

    def __init__(self, records: Iterable[LicenseRecord] | None = None, evidence_records: dict[str, dict[str, Any]] | None = None, source_records: dict[str, dict[str, Any]] | None = None) -> None:
        self.records: list[LicenseRecord] = list(records or [])
        self.evidence_records = dict(evidence_records or {})
        self.source_records = dict(source_records or {})

    @classmethod
    def from_json(cls, path: str | Path) -> "LicensingDB":
        """Load licensing records from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        records = [
            LicenseRecord(
                vendor=str(item["vendor"]),
                license_id=str(item["license_id"]),
                tier=str(item["tier"]),
                feature_set=tuple(str(value) for value in item.get("feature_set", [])),
                production_eligible=bool(item.get("production_eligible", False)),
                verification_state=str(item.get("verification_state", "requires_evidence")),
                evidence_ids=tuple(str(value) for value in item.get("evidence_ids", [])),
                source_ids=tuple(str(value) for value in item.get("source_ids", [])),
                support_scope=str(item.get("support_scope", "")),
                term_months=item.get("term_months"),
                confidence=float(item.get("confidence", 0.0)),
            ) for item in payload.get("licenses", [])
        ]
        evidence = {str(item.get("evidence_id", key)): item for key, item in enumerate(payload.get("evidence_records", []))} if isinstance(payload.get("evidence_records"), list) else payload.get("evidence_records", {})
        sources = {str(item.get("source_id", key)): item for key, item in enumerate(payload.get("source_records", []))} if isinstance(payload.get("source_records"), list) else payload.get("source_records", {})
        return cls(records, evidence, sources)

    def register(self, record: LicenseRecord) -> None:
        """Register a license record."""
        if not 0.0 <= record.confidence <= 1.0:
            raise ValueError("license confidence must be between zero and one")
        self.records.append(record)

    def lookup(self, vendor: str, license_id: str) -> LicenseRecord | None:
        """Find a license by vendor and identifier."""
        return next((record for record in self.records if record.vendor.lower() == vendor.lower() and record.license_id.lower() == license_id.lower()), None)

    def _evidence_usable(self, evidence_id: str) -> bool:
        evidence = self.evidence_records.get(evidence_id)
        if not evidence or evidence.get("verification_state") != "verified":
            return False
        if bool(evidence.get("revoked", False)) or bool(evidence.get("expired", False)):
            return False
        source_id = evidence.get("source_id")
        source = self.source_records.get(str(source_id)) if source_id else None
        return source is None or bool(source.get("verified", False))

    def has_verified_entitlement(self, vendor: str, license_id: str, feature: str, production: bool = True) -> tuple[bool, str, tuple[str, ...], float]:
        """Check whether a license authoritatively covers one feature."""
        record = self.lookup(vendor, license_id)
        if record is None:
            return False, "license_record_not_found", (), 0.0
        if feature.lower() not in {item.lower() for item in record.feature_set}:
            return False, "feature_not_in_license_scope", tuple(record.evidence_ids), 0.0
        if production and not record.production_eligible:
            return False, "license_not_production_eligible", tuple(record.evidence_ids), 0.0
        if record.verification_state != "verified":
            return False, "license_evidence_not_verified", tuple(record.evidence_ids), 0.0
        if not record.evidence_ids or not all(self._evidence_usable(item) for item in record.evidence_ids):
            return False, "license_evidence_chain_incomplete", tuple(record.evidence_ids), 0.0
        return True, "license_entitlement_verified", tuple(record.evidence_ids), record.confidence

    def requirements_for(self, features: Iterable[str], vendor: str | None = None) -> dict[str, list[str]]:
        """Return license IDs that cover each requested feature."""
        return {feature: [record.license_id for record in self.records if (vendor is None or record.vendor.lower() == vendor.lower()) and feature.lower() in {item.lower() for item in record.feature_set}] for feature in features}
