from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from auth.rbac import Principal
from auth.session_manager import SessionError, SessionManager


def test_session_manager_creates_validates_and_revokes_sessions():
    with tempfile.TemporaryDirectory() as directory:
        manager = SessionManager(Path(directory) / "sessions.json")
        record = manager.create(Principal("alice", ("viewer",)), ttl_seconds=60)
        principal = manager.validate(record.session_id)
        assert principal.username == "alice"
        assert principal.session_id == record.session_id
        manager.revoke(record.session_id)
        try:
            manager.validate(record.session_id)
        except SessionError:
            pass
        else:
            raise AssertionError("revoked session must be rejected")


def test_session_manager_expires_and_cleans_sessions():
    with tempfile.TemporaryDirectory() as directory:
        manager = SessionManager(Path(directory) / "sessions.json")
        record = manager.create(Principal("alice", ("viewer",)), ttl_seconds=1)
        now = datetime.fromisoformat(record.expires_at) + timedelta(seconds=1)
        try:
            manager.validate(record.session_id, now)
        except SessionError:
            pass
        else:
            raise AssertionError("expired session must be rejected")
        assert manager.cleanup(now) >= 1
