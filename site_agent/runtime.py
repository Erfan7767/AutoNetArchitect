"""Enrolled local-agent runtime that permits only scoped read-only discovery."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from .agent import ReadOnlyCollector, ReadOnlyDiscoveryAgent
from .enrollment import EnrollmentReceipt
from .models import AgentHealth, DiscoveryResult, DiscoveryTarget
from .scope import AuthorizedScope


class EnrolledReadOnlyAgent:
    """Bind an active mutual-enrollment receipt to one acknowledged discovery scope."""

    def __init__(self, receipt: EnrollmentReceipt, scope: AuthorizedScope, collector: ReadOnlyCollector, now: Callable[[], datetime] | None = None) -> None:
        """Reject startup unless the receipt matches the exact locally acknowledged scope."""

        self._now = now or (lambda: datetime.now(timezone.utc))
        if not receipt.valid_for(receipt.agent_id, scope.site_id, scope.evidence_hash(), self._now()):
            raise ValueError("An active read-only enrollment receipt matching the local acknowledged scope is required.")
        self._receipt = receipt
        self._scope = scope
        self._discovery = ReadOnlyDiscoveryAgent(scope, collector)

    @property
    def agent_id(self) -> str:
        """Return the enrolled non-secret agent identifier."""

        return self._receipt.agent_id

    def health(self) -> AgentHealth:
        """Report enrollment health without contact attempts, credentials, or secret material."""

        valid = self._receipt.valid_for(self._receipt.agent_id, self._scope.site_id, self._scope.evidence_hash(), self._now())
        return AgentHealth(
            agent_id=self._receipt.agent_id,
            site_id=self._scope.site_id,
            observed_at=self._now(),
            healthy=valid,
            detail="Active mutual enrollment is bound to the acknowledged read-only discovery scope." if valid else "Enrollment receipt is inactive, expired, or no longer matches the acknowledged discovery scope.",
        )

    def discover(self, target: DiscoveryTarget) -> DiscoveryResult:
        """Run the injected collector only if the active receipt and local scope remain valid."""

        if not self.health().healthy:
            raise RuntimeError("Read-only discovery is blocked because mutual enrollment is no longer active for this scope.")
        return self._discovery.discover(target)
