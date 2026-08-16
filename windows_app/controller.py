"""Application controller that binds Windows UI input to the approved read-only site agent."""

from __future__ import annotations

from site_agent.agent import ReadOnlyCollector, ReadOnlyDiscoveryAgent
from site_agent.models import DiscoveryResult, DiscoveryTarget
from site_agent.scope import AuthorizedScope

from .workspace import WindowsWorkspace


class WindowsDiscoveryController:
    """Coordinates explicit discovery approval and secret-free read-only evidence collection."""

    def __init__(self, workspace: WindowsWorkspace, collector: ReadOnlyCollector) -> None:
        """Create a controller with injected read-only collection behavior."""

        self._workspace = workspace
        self._collector = collector

    def approve_scope(self, scope: AuthorizedScope) -> None:
        """Save a human-approved scope before any discovery target can be evaluated."""

        if not scope.operator_acknowledged:
            raise PermissionError("The operator must explicitly acknowledge the read-only discovery boundary.")
        self._workspace.save_scope(scope)

    def approved_scope(self) -> AuthorizedScope | None:
        """Return the locally approved scope without exposing workspace implementation details."""

        return self._workspace.load_scope()

    def discover_target(self, target: DiscoveryTarget) -> DiscoveryResult:
        """Run the read-only collector only after loading a valid local approval scope."""

        scope = self._workspace.load_scope()
        if scope is None:
            raise PermissionError("Discovery is blocked until a human-approved local scope is saved.")
        agent = ReadOnlyDiscoveryAgent(scope, self._collector)
        return agent.discover(target)
