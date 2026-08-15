"""CLI authentication and permission helpers."""
from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
from typing import Callable

from auth.auth_manager import AuthenticationError
from auth.rbac import PermissionDenied

from .context import CLIContext, CLIResult


@dataclass
class AuthHandler:
    """Adapter for local authentication and session commands."""

    context: CLIContext
    password_fn: Callable[[str], str] = getpass

    def login(self, username: str, password: str | None = None, *, ttl_seconds: int = 3600) -> CLIResult:
        """Authenticate a principal using a supplied or prompted password."""
        secret = password if password is not None else self.password_fn("Password: ")
        return self.context.login(username, secret, ttl_seconds=ttl_seconds)

    def logout(self) -> CLIResult:
        """Revoke the current local session."""
        return self.context.logout()

    def whoami(self) -> CLIResult:
        """Return current principal metadata."""
        return self.context.whoami()

    def require(self, permission: str) -> None:
        """Expose permission enforcement for command adapters."""
        try:
            self.context.require(permission)
        except (PermissionDenied, AuthenticationError):
            raise
