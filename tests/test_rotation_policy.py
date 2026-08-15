from datetime import datetime, timedelta, timezone

from secrets.rotation_policy import RotationPolicy
from secrets.secret_manager import SecretMetadata


def metadata(last_rotated: datetime, interval: int = 90, expires_at: str | None = None) -> SecretMetadata:
    return SecretMetadata("id", "purpose", "owner", last_rotated_at=last_rotated.isoformat(), rotation_interval_days=interval, expires_at=expires_at)


def test_rotation_policy_classifies_lifecycle_states():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    policy = RotationPolicy(warning_days=14)
    assert policy.evaluate(metadata(now - timedelta(days=10)), now).status == "current"
    assert policy.evaluate(metadata(now - timedelta(days=80)), now).status == "due_soon"
    assert policy.evaluate(metadata(now - timedelta(days=100)), now).status == "overdue"
    assert policy.evaluate(metadata(now - timedelta(days=1), expires_at=(now - timedelta(hours=1)).isoformat()), now).status == "expired"
    assert policy.evaluate(metadata(now, interval=0), now).status == "blocked_invalid_policy"
