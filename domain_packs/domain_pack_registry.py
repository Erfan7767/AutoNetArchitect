from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainPackRecord:
    """Registry metadata for one supported sector pack."""

    pack_id: str
    display_name: str
    module_path: str
    supported_sectors: tuple[str, ...]
    incompatible_with: tuple[str, ...] = ()
    integration_targets: tuple[str, ...] = ()
    production_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class DomainPackRegistry:
    """Central registry for supported production sector packs."""

    def __init__(self, records: list[DomainPackRecord] | None = None) -> None:
        self._records = {record.pack_id: record for record in (records or self.default_records())}

    @staticmethod
    def default_records() -> list[DomainPackRecord]:
        return [
            DomainPackRecord("enterprise_corporate", "Enterprise Corporate Networks", "domain_packs.enterprise_corporate", ("enterprise_corporate", "corporate_enterprise"), ("banking", "hospital_clinical", "university_campus"), ("requirements", "design", "equipment", "compliance")),
            DomainPackRecord("banking", "Banking Networks", "domain_packs.banking", ("banking", "bank"), ("enterprise_corporate", "hospital_clinical", "university_campus"), ("requirements", "governance", "security", "deployment", "compliance")),
            DomainPackRecord("hospital_clinical", "Hospital and Clinical Networks", "domain_packs.hospital_clinical", ("hospital", "healthcare", "hospital_clinical", "clinical"), ("enterprise_corporate", "banking", "university_campus"), ("requirements", "security", "wireless", "field_reality", "compliance")),
            DomainPackRecord("university_campus", "University and Campus Networks", "domain_packs.university_campus", ("university", "higher_education", "education", "university_campus"), ("enterprise_corporate", "banking", "hospital_clinical"), ("requirements", "wireless", "security", "services", "operations")),
        ]

    def list_records(self) -> list[DomainPackRecord]:
        return list(self._records.values())

    def get(self, pack_id: str) -> DomainPackRecord | None:
        return self._records.get(pack_id)

    def find_by_sector(self, sector: str) -> list[DomainPackRecord]:
        value = sector.lower()
        return [record for record in self._records.values() if value in record.supported_sectors]

    def register(self, record: DomainPackRecord) -> None:
        if record.pack_id in self._records:
            raise ValueError(f"Domain pack {record.pack_id!r} is already registered")
        self._records[record.pack_id] = record

    def snapshot(self) -> list[dict[str, Any]]:
        return [{"pack_id": record.pack_id, "display_name": record.display_name, "module_path": record.module_path, "supported_sectors": list(record.supported_sectors), "production_enabled": record.production_enabled} for record in self.list_records()]
