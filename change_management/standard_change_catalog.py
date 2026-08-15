"""Local standard-change catalog with review and usage controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable

from .change_models import ChangeRequest, ChangeType, RiskLevel


@dataclass
class StandardChange:
    """One pre-approved standard change catalog entry."""

    catalog_id: str
    title: str
    description: str
    scope_limitation: str
    risk_level: str
    pre_approved_by: str
    approval_date: date
    review_date: date
    implementation_template: str
    rollback_template: str
    verification_template: str
    usage_count: int = 0
    last_used: datetime | None = None
    success_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize catalog entry."""
        return asdict(self) | {"approval_date": self.approval_date.isoformat(), "review_date": self.review_date.isoformat(), "last_used": self.last_used.isoformat() if self.last_used else None}


class StandardChangeCatalog:
    """Maintain pre-approved catalog entries with annual review discipline."""

    def __init__(self, entries: Iterable[StandardChange] = ()) -> None:
        """Create a catalog and reject non-low-risk standard entries."""
        self._entries: dict[str, StandardChange] = {}
        for entry in entries:
            self.register(entry)

    def register(self, entry: StandardChange) -> StandardChange:
        """Register a standard entry only when its risk is low."""
        if entry.risk_level != RiskLevel.LOW.value:
            raise ValueError("standard change catalog entries must be low risk")
        self._entries[entry.catalog_id] = entry
        return entry

    def get(self, catalog_id: str) -> StandardChange:
        """Return one catalog entry."""
        try:
            return self._entries[catalog_id]
        except KeyError as exc:
            raise KeyError(f"standard catalog entry not found: {catalog_id}") from exc

    def list(self) -> tuple[StandardChange, ...]:
        """Return catalog entries in deterministic order."""
        return tuple(self._entries[key] for key in sorted(self._entries))

    def eligible(self, request: ChangeRequest, *, today: date | None = None) -> tuple[StandardChange, ...]:
        """Return active entries whose scope and review date are valid."""
        current = today or date.today()
        if request.change_type not in {ChangeType.STANDARD.value, ChangeType.NORMAL.value}:
            return ()
        result = []
        for entry in self._entries.values():
            if entry.review_date < current or entry.success_rate < 0.8:
                continue
            if len(request.affected_devices) <= 1 and entry.scope_limitation:
                result.append(entry)
        return tuple(sorted(result, key=lambda item: item.catalog_id))

    def record_use(self, catalog_id: str, *, successful: bool, when: datetime | None = None) -> StandardChange:
        """Update usage and success metrics for a catalog item."""
        entry = self.get(catalog_id)
        previous = entry.usage_count
        entry.usage_count += 1
        entry.success_rate = ((entry.success_rate * previous) + (1.0 if successful else 0.0)) / entry.usage_count
        entry.last_used = when or datetime.now(timezone.utc)
        return entry

    def due_for_review(self, *, today: date | None = None) -> tuple[StandardChange, ...]:
        """Return entries whose annual review date has arrived."""
        current = today or date.today()
        return tuple(entry for entry in self.list() if entry.review_date <= current)

    def remove_low_success(self, threshold: float = 0.8) -> tuple[str, ...]:
        """Remove entries below the configured success threshold."""
        removed = tuple(sorted(entry.catalog_id for entry in self._entries.values() if entry.success_rate < threshold))
        for catalog_id in removed:
            self._entries.pop(catalog_id, None)
        return removed
