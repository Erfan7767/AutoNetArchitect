"""Tests for CLI authentication adapter."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from auth.auth_manager import AuthManager
from audit.audit_trail import AuditTrail
from cli.auth_handler import AuthHandler
from cli.context import CLIContext, CLISettings


def test_auth_handler_login_whoami_logout():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = AuditTrail(root / "audit.jsonl")
        context = CLIContext(CLISettings(root=root), audit_trail=audit)
        context.auth_manager.create_user("engineer", "strong-password-123", ("designer",))
        handler = AuthHandler(context)
        logged = handler.login("engineer", "strong-password-123")
        assert logged.success is True
        assert handler.whoami().data["username"] == "engineer"
        assert handler.logout().status == "logged_out"
        assert context.session_id is None


def test_auth_handler_rejects_invalid_password():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        context = CLIContext(CLISettings(root=root))
        context.auth_manager.create_user("engineer", "strong-password-123", ("viewer",))
        rejected = False
        try:
            AuthHandler(context).login("engineer", "wrong-password")
        except Exception:
            rejected = True
        if not rejected:
            raise AssertionError("invalid password should be rejected")
