"""Role-based access control for AutoNetArchitect V1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class PermissionDenied(PermissionError):
    """Raised when a principal lacks a required permission."""


@dataclass(frozen=True)
class RoleDefinition:
    """Named role with a stable set of permissions."""

    name: str
    permissions: frozenset[str]
    description: str = ""


@dataclass(frozen=True)
class Principal:
    """Authenticated subject used by the authorization boundary."""

    username: str
    roles: tuple[str, ...]
    session_id: str | None = None


class RBAC:
    """Evaluate permissions using explicit role definitions."""

    WILDCARD = "*"

    def __init__(self, roles: Iterable[RoleDefinition] | None = None) -> None:
        self._roles: dict[str, RoleDefinition] = {}
        for role in self.default_roles():
            self.register_role(role)
        for role in roles or ():
            self.register_role(role)

    @staticmethod
    def default_roles() -> tuple[RoleDefinition, ...]:
        """Return conservative V1 roles."""
        return (
            RoleDefinition("viewer", frozenset({"project.read", "config.read", "audit.read"}), "Read-only project and audit access."),
            RoleDefinition("designer", frozenset({"project.read", "project.write", "config.read", "config.generate", "audit.read"}), "Design and preview generation access."),
            RoleDefinition("operator", frozenset({"project.read", "config.read", "config.generate", "deployment.preview", "deployment.execute", "rollback.execute", "audit.read", "audit.write"}), "Operational deployment and rollback access."),
            RoleDefinition("security_admin", frozenset({"project.read", "config.read", "secret.metadata.read", "pki.manage", "audit.read", "audit.write"}), "Security metadata and PKI administration without secret values."),
            RoleDefinition("admin", frozenset({RBAC.WILDCARD}), "Full administrative access."),
        )

    def register_role(self, role: RoleDefinition) -> None:
        """Register or replace a role definition."""
        if not role.name or any(not permission for permission in role.permissions):
            raise ValueError("role name and permissions must be non-empty")
        self._roles[role.name] = role

    def role(self, name: str) -> RoleDefinition:
        """Return one role definition."""
        try:
            return self._roles[name]
        except KeyError as exc:
            raise KeyError(f"unknown role: {name}") from exc

    def roles(self) -> tuple[RoleDefinition, ...]:
        """List roles deterministically."""
        return tuple(self._roles[key] for key in sorted(self._roles))

    def permissions_for(self, role_names: Iterable[str]) -> frozenset[str]:
        """Resolve the union of permissions for role names."""
        permissions: set[str] = set()
        for role_name in role_names:
            permissions.update(self.role(str(role_name)).permissions)
        return frozenset(permissions)

    def has_permission(self, principal: Principal, permission: str) -> bool:
        """Return whether a principal is allowed to perform a permission."""
        permissions = self.permissions_for(principal.roles)
        if self.WILDCARD in permissions or permission in permissions:
            return True
        resource = permission.split(".", 1)[0] + ".*"
        return resource in permissions

    def enforce(self, principal: Principal, permission: str) -> None:
        """Raise PermissionDenied when permission is absent."""
        if not self.has_permission(principal, permission):
            raise PermissionDenied(f"principal {principal.username!r} lacks permission {permission!r}")
