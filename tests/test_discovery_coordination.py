"""Tests for safe parallel distribution of authorized discovery work."""

from site_agent.coordination import AgentAssignment, AgentRole
from site_agent.discovery_coordination import DiscoveryWorkItem, ParallelDiscoveryCoordinator
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, ObservedDeviceFacts
from site_agent.scope import AuthorizedScope


def _scope() -> AuthorizedScope:
    """Build a narrow acknowledged scope shared by test work items."""

    return AuthorizedScope(
        site_id="site-1",
        approved_networks=("10.0.0.0/24",),
        approved_targets=("10.0.0.10", "10.0.0.11"),
        allowed_protocols=(ManagementProtocol.HTTPS_API,),
        approval_reference="approval-1",
        operator_acknowledged=True,
    )


def _item(address: str, agent_id: str) -> DiscoveryWorkItem:
    """Create one properly scoped discovery assignment."""

    return DiscoveryWorkItem(
        assignment=AgentAssignment(
            agent_id=agent_id,
            role=AgentRole.AUTHORIZED_DISCOVERY,
            site_id="site-1",
            scope_hash="scope-1",
            authority_reference="approval-1",
        ),
        target=DiscoveryTarget(
            address=address,
            protocol=ManagementProtocol.HTTPS_API,
            credential_reference=f"credential-{address}",
        ),
    )


def test_parallel_batch_preserves_input_order_and_collector_evidence() -> None:
    """Authorized independent targets may be handled concurrently without mutating evidence."""

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        return DiscoveryResult(
            target=target,
            state=DiscoveryState.DISCOVERED,
            facts=ObservedDeviceFacts(
                vendor="Cisco",
                platform="Catalyst",
                software_version="17.18.1",
                serial_reference=f"serial-{target.address}",
                interface_count=24,
            ),
            message="Observed through an approved read-only collector.",
        )

    result = ParallelDiscoveryCoordinator(_scope(), "scope-1", collector, max_workers=2).run(
        (_item("10.0.0.10", "agent-a"), _item("10.0.0.11", "agent-b"))
    )

    assert [item.result.target.address for item in result.results] == ["10.0.0.10", "10.0.0.11"]
    assert [item.result.state for item in result.results] == [DiscoveryState.DISCOVERED, DiscoveryState.DISCOVERED]
    assert not result.has_unresolved_results


def test_scope_mismatch_blocks_dispatch_before_collector_is_called() -> None:
    """A coordinator refuses a different scope even when the target address is valid."""

    calls: list[str] = []

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        calls.append(target.address)
        raise AssertionError("Collector must not be called for a mismatched assignment.")

    bad_item = _item("10.0.0.10", "agent-a").model_copy(update={"assignment": AgentAssignment(
        agent_id="agent-a",
        role=AgentRole.AUTHORIZED_DISCOVERY,
        site_id="site-1",
        scope_hash="different-scope",
        authority_reference="approval-1",
    )})

    coordinator = ParallelDiscoveryCoordinator(_scope(), "scope-1", collector)
    try:
        coordinator.run((bad_item,))
    except ValueError as error:
        assert "active approved scope" in str(error)
    else:
        raise AssertionError("A scope mismatch must block dispatch.")
    assert calls == []


def test_collector_failure_becomes_ambiguous_no_guess_result() -> None:
    """Unsafe collector output cannot turn into invented discovered device facts."""

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        raise RuntimeError(f"untrusted error for {target.address}")

    result = ParallelDiscoveryCoordinator(_scope(), "scope-1", collector).run((_item("10.0.0.10", "agent-a"),))

    assert result.has_unresolved_results
    assert result.results[0].result.state is DiscoveryState.AMBIGUOUS
    assert result.results[0].result.facts is None
    assert "safely bound" in result.results[0].result.message
