"""Protocol-bound read-only collection orchestration for approved local discovery targets.

Concrete transports are supplied by the Windows installer or a vendor-supported
plugin. The orchestrator never constructs CLI commands, resolves credentials, or
permits a write-capable operation: an authorized scope and a credential reference
must already exist before a transport session is asked for evidence.
"""

from __future__ import annotations

from typing import Protocol

from .discovery_adapters import DiscoveryPlan, VendorDiscoveryAdapter
from .models import DiscoveryResult, DiscoveryState, DiscoveryTarget
from .scope import AuthorizedScope
from .vendor_support import VendorFamily


class ReadOnlyProtocolSession(Protocol):
    """Execute an already-reviewed read-only vendor discovery plan using external credential resolution."""

    def collect(self, target: DiscoveryTarget, plan: DiscoveryPlan) -> DiscoveryResult:
        """Return evidence for exactly the requested target without changing device state."""


class ReadOnlyProtocolSessionProvider(Protocol):
    """Open a protocol session bound to an external credential reference and no raw secret value."""

    def open_read_only(self, target: DiscoveryTarget) -> ReadOnlyProtocolSession:
        """Return a session only after the local credential provider approves the reference."""


class AuthorizedProtocolDiscoveryCollector:
    """Collect vendor evidence only through scope-authorized read-only protocol plans."""

    def __init__(self, scope: AuthorizedScope, adapter: VendorDiscoveryAdapter, session_provider: ReadOnlyProtocolSessionProvider) -> None:
        """Bind a vendor adapter to one acknowledged local scope and credential-isolated session provider."""

        self._scope = scope
        self._adapter = adapter
        self._session_provider = session_provider

    @property
    def vendor_family(self) -> VendorFamily:
        """Return the vendor family whose read-only plan this collector can request."""

        return self._adapter.family

    def collect(self, target: DiscoveryTarget) -> DiscoveryResult:
        """Return bounded discovery evidence or a fail-closed result before any unauthorized session opens."""

        if not self._scope.authorizes(target):
            return DiscoveryResult(
                target=target,
                state=DiscoveryState.UNAUTHORIZED,
                message="Target or management protocol is outside the acknowledged approved discovery scope.",
            )
        if target.credential_reference == "local-inventory/no-credential-resolved":
            return DiscoveryResult(
                target=target,
                state=DiscoveryState.UNAUTHORIZED,
                message="A credential reference assignment is required before protocol-specific read-only collection.",
            )
        plan = self._adapter.plan(target)
        self._assert_read_only_plan(plan, target)
        session = self._session_provider.open_read_only(target)
        result = session.collect(target, plan)
        if result.target != target:
            raise ValueError("Read-only protocol session returned evidence for a different target.")
        return result

    @staticmethod
    def _assert_read_only_plan(plan: DiscoveryPlan, target: DiscoveryTarget) -> None:
        """Reject a plan if its vendor, protocol, credential reference, or operation mode is unsafe."""

        if plan.target != target or plan.execution_mode != "read_only_only":
            raise ValueError("Protocol collector rejected a plan that is not bound to the requested read-only target.")
        if not plan.requests or any(not request.read_only or request.protocol != target.protocol for request in plan.requests):
            raise ValueError("Protocol collector rejected a plan containing a non-read-only or protocol-mismatched request.")
        if any(request.credential_reference != target.credential_reference for request in plan.requests):
            raise ValueError("Protocol collector rejected a plan whose credential reference differs from the assigned target reference.")
