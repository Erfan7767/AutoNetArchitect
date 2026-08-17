"""Tests for scope-, protocol-, and credential-reference-bound read-only collection."""

from __future__ import annotations

from dataclasses import dataclass

from site_agent.discovery_adapters import CiscoDiscoveryAdapter
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol
from site_agent.protocol_collectors import AuthorizedProtocolDiscoveryCollector
from site_agent.scope import AuthorizedScope


@dataclass
class RecordingSession:
    """Test session that records the approved plan without opening a real device connection."""

    calls: list[tuple[DiscoveryTarget, object]]

    def collect(self, target: DiscoveryTarget, plan) -> DiscoveryResult:
        """Return one read-only discovery result for the exact target."""

        self.calls.append((target, plan))
        return DiscoveryResult(target=target, state=DiscoveryState.AMBIGUOUS, message="Read-only protocol evidence requires reviewer interpretation.")


@dataclass
class RecordingProvider:
    """Test credential-isolated session provider with no credential value field."""

    session: RecordingSession
    opened: list[DiscoveryTarget]

    def open_read_only(self, target: DiscoveryTarget) -> RecordingSession:
        """Record opening only after the collector authorizes the target."""

        self.opened.append(target)
        return self.session


def scope() -> AuthorizedScope:
    """Create an acknowledged scope allowing a single HTTPS target."""

    return AuthorizedScope(
        site_id="site-protocol-001",
        approved_networks=("10.60.0.0/24",),
        approved_targets=("10.60.0.10",),
        allowed_protocols=(ManagementProtocol.HTTPS_API,),
        approval_reference="human-scope-protocol-001",
        operator_acknowledged=True,
    )


def test_protocol_collector_opens_a_session_only_after_scope_and_reference_checks() -> None:
    """A scoped target with an assigned reference reaches only the vendor read-only plan session."""

    session = RecordingSession([])
    provider = RecordingProvider(session, [])
    collector = AuthorizedProtocolDiscoveryCollector(scope(), CiscoDiscoveryAdapter(), provider)
    target = DiscoveryTarget(address="10.60.0.10", protocol=ManagementProtocol.HTTPS_API, credential_reference="credential-ref-https-001")

    result = collector.collect(target)

    assert result.state is DiscoveryState.AMBIGUOUS
    assert provider.opened == [target]
    assert len(session.calls) == 1
    plan = session.calls[0][1]
    assert plan.execution_mode == "read_only_only"
    assert all(request.read_only for request in plan.requests)
    assert all(request.credential_reference == "credential-ref-https-001" for request in plan.requests)


def test_protocol_collector_refuses_out_of_scope_or_unassigned_targets_before_opening_a_session() -> None:
    """No session opens if a target is outside scope or still lacks assigned credentials."""

    session = RecordingSession([])
    provider = RecordingProvider(session, [])
    collector = AuthorizedProtocolDiscoveryCollector(scope(), CiscoDiscoveryAdapter(), provider)

    outside = collector.collect(DiscoveryTarget(address="10.60.0.11", protocol=ManagementProtocol.HTTPS_API, credential_reference="credential-ref-https-001"))
    unassigned = collector.collect(DiscoveryTarget(address="10.60.0.10", protocol=ManagementProtocol.HTTPS_API, credential_reference="local-inventory/no-credential-resolved"))

    assert outside.state is DiscoveryState.UNAUTHORIZED
    assert unassigned.state is DiscoveryState.UNAUTHORIZED
    assert provider.opened == []
    assert session.calls == []
