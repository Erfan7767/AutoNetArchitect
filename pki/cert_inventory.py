"""Certificate inventory with expiry and revocation tracking."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CertificateRecord:
    """Public certificate metadata; no private key material is stored."""

    cert_id: str
    subject: str
    sans: tuple[str, ...]
    serial_number: str
    issuer: str
    not_before: str
    not_after: str
    certificate_path: str
    private_key_ref: str
    status: str = "active"
    key_algorithm: str = "RSA-2048"
    revocation_date: str | None = None
    revocation_reason: str | None = None
    renewal_window_days: int = 30
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize public metadata only."""
        return asdict(self) | {"sans": list(self.sans)}


class CertInventory:
    """Persist and query certificate metadata without private key values."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: dict[str, CertificateRecord] = {}
        self._load()

    def register(self, record: CertificateRecord) -> CertificateRecord:
        """Add or replace a certificate record."""
        if not record.private_key_ref.startswith("secret://"):
            raise ValueError("private key inventory entries must be secret:// references")
        self._records[record.cert_id] = record
        self._persist()
        return record

    def get(self, cert_id: str) -> CertificateRecord:
        """Return one certificate record."""
        try:
            return self._records[cert_id]
        except KeyError as exc:
            raise KeyError(f"certificate not found: {cert_id}") from exc

    def list(self, include_revoked: bool = True) -> tuple[CertificateRecord, ...]:
        """List records in deterministic order."""
        values = self._records.values() if include_revoked else (record for record in self._records.values() if record.status != "revoked")
        return tuple(sorted(values, key=lambda record: record.cert_id))

    def expiring(self, within_days: int = 30, now: datetime | None = None) -> tuple[CertificateRecord, ...]:
        """Return active certificates expiring within the requested window."""
        if within_days < 0:
            raise ValueError("within_days must not be negative")
        now = now or datetime.now(timezone.utc)
        result: list[CertificateRecord] = []
        for record in self.list(include_revoked=False):
            expiry = self._parse(record.not_after)
            remaining = (expiry - now).total_seconds()
            if 0 <= remaining <= within_days * 86400:
                result.append(record)
        return tuple(result)

    def status(self, cert_id: str, now: datetime | None = None) -> str:
        """Return current, due_soon, expired, or revoked status."""
        record = self.get(cert_id)
        if record.status == "revoked":
            return "revoked"
        now = now or datetime.now(timezone.utc)
        expiry = self._parse(record.not_after)
        if now >= expiry:
            return "expired"
        if now + timedelta(days=record.renewal_window_days) >= expiry:
            return "due_soon"
        return "active"

    def revoke(self, cert_id: str, reason: str, when: datetime | None = None) -> CertificateRecord:
        """Mark a certificate revoked in the inventory."""
        record = self.get(cert_id)
        revoked = CertificateRecord(record.cert_id, record.subject, record.sans, record.serial_number, record.issuer, record.not_before, record.not_after, record.certificate_path, record.private_key_ref, "revoked", record.key_algorithm, (when or datetime.now(timezone.utc)).isoformat(), reason, record.renewal_window_days, record.version)
        self._records[cert_id] = revoked
        self._persist()
        return revoked

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        for cert_id, item in payload.items():
            self._records[cert_id] = CertificateRecord(cert_id=cert_id, subject=str(item["subject"]), sans=tuple(item.get("sans", [])), serial_number=str(item["serial_number"]), issuer=str(item["issuer"]), not_before=str(item["not_before"]), not_after=str(item["not_after"]), certificate_path=str(item["certificate_path"]), private_key_ref=str(item["private_key_ref"]), status=str(item.get("status", "active")), key_algorithm=str(item.get("key_algorithm", "RSA-2048")), revocation_date=item.get("revocation_date"), revocation_reason=item.get("revocation_reason"), renewal_window_days=int(item.get("renewal_window_days", 30)), version=int(item.get("version", 1)))

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {cert_id: record.to_dict() for cert_id, record in sorted(self._records.items())}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
