"""Read-only discovery orchestration with strict local scope enforcement."""

from __future__ import annotations

from collections.abc import Callable

from .models import DiscoveryResult, DiscoveryState, DiscoveryTarget
from .scope import AuthorizedScope

ReadOnlyCollector = Callable[[DiscoveryTarget], DiscoveryResult]


class ReadOnlyDiscoveryAgent:
    """Runs an injected read-only collector only for a human-approved local target scope."""

    def __init__(self, scope: AuthorizedScope, collector: ReadOnlyCollector) -> None:
        """Create an agent with an explicit scope and a non-mutating collector implementation."""

        self._scope = scope
        self._collector = collector

    def discover(self, target: DiscoveryTarget) -> DiscoveryResult:
        """Collect device facts or return an authorization result without connecting out of scope."""

        if not self._scope.authorizes(target):
            return DiscoveryResult(
                target=target,
                state=DiscoveryState.UNAUTHORIZED,
                message="Target or management protocol is outside the approved site scope.",
            )
        result = self._collector(target)
        if result.target != target:
            raise ValueError("Collector returned evidence for a different target.")
        return result
