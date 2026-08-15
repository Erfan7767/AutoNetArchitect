from pathlib import Path
import tempfile

from audit.audit_trail import AuditTrail
from auth.auth_manager import AuthManager, AuthenticationError


def test_local_auth_hashes_password_and_authenticates_principal():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        trail = AuditTrail(root / "audit.jsonl")
        manager = AuthManager(root / "users.json", audit_trail=trail)
        user = manager.create_user("alice", "correct horse battery staple", ("designer",))
        assert user.password_hash != "correct horse battery staple"
        assert "correct horse battery staple" not in (root / "users.json").read_text(encoding="utf-8")
        principal = manager.authenticate("alice", "correct horse battery staple")
        assert principal.username == "alice"
        assert principal.roles == ("designer",)
        assert any(entry.event_type == "auth.login_success" for entry in trail.entries())


def test_auth_rejects_invalid_password_and_inactive_user():
    with tempfile.TemporaryDirectory() as directory:
        manager = AuthManager(Path(directory) / "users.json")
        manager.create_user("bob", "correct horse battery staple")
        try:
            manager.authenticate("bob", "wrong password with length")
        except AuthenticationError:
            pass
        else:
            raise AssertionError("invalid password should be rejected")
        manager.set_active("bob", False)
        try:
            manager.authenticate("bob", "correct horse battery staple")
        except AuthenticationError:
            return
        raise AssertionError("inactive user should be rejected")
