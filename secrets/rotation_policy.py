"""Secret rotation scheduling policy based only on metadata."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .secret_manager import SecretMetadata


@dataclass(frozen=True)
class RotationDecision:
    """Auditable rotation decision."""

    secret_id: str
    status: str
    due_at: str | None
    reason: str
    required_action: str


class RotationPolicy:
    """Evaluate rotation health without accessing plaintext secret material."""

    def __init__(self, warning_days: int = 14, maximum_interval_days: int = 365) -> None:
        if warning_days < 0 or maximum_interval_days <= 0:
            raise ValueError("rotation policy limits must be positive")
        self.warning_days = warning_days
        self.maximum_interval_days = maximum_interval_days

    def evaluate(self, metadata: SecretMetadata, now: datetime | None = None) -> RotationDecision:
        """Return a rotation decision for one metadata record."""
        now = now or datetime.now(timezone.utc)
        if metadata.rotation_interval_days <= 0 or metadata.rotation_interval_days > self.maximum_interval_days:
            return RotationDecision(metadata.secret_id, "blocked_invalid_policy", None, "rotation interval is outside policy bounds", "correct metadata before production use")
        if not metadata.last_rotated_at:
            return RotationDecision(metadata.secret_id, "overdue", None, "secret has never been rotated", "rotate immediately")
        rotated = self._parse(metadata.last_rotated_at)
        due = rotated + timedelta(days=metadata.rotation_interval_days)
        due_iso = due.isoformat()
        if metadata.expires_at:
            expires = self._parse(metadata.expires_at)
            if now >= expires:
                return RotationDecision(metadata.secret_id, "expired", due_iso, "metadata expiry has passed", "revoke and replace before use")
        if now >= due:
            return RotationDecision(metadata.secret_id, "overdue", due_iso, "rotation interval has elapsed", "rotate immediately")
        if now + timedelta(days=self.warning_days) >= due:
            return RotationDecision(metadata.secret_id, "due_soon", due_iso, "rotation deadline is within warning window", "schedule rotation")
        return RotationDecision(metadata.secret_id, "current", due_iso, "secret is within rotation policy", "no immediate action")

    def evaluate_all(self, metadata: tuple[SecretMetadata, ...], now: datetime | None = None) -> tuple[RotationDecision, ...]:
        """Evaluate all metadata in deterministic order."""
        return tuple(self.evaluate(item, now) for item in metadata)

    @staticmethod
    def _parse(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid ISO-8601 timestamp: {value}") from exc
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
