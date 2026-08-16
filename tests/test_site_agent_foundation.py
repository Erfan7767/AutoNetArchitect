"""Tests for the local, read-only AutoNetArchitect site-agent foundation."""

from site_agent.agent import ReadOnlyDiscoveryAgent
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, VirtualTestResult, VirtualTestState
from site_agent.scope import AuthorizedScope
from site_agent.virtual_validation import VirtualValidationCoordinator


def test_read_only_agent_blocks_target_outside_approved_scope() -> None:
    """The agent must not invoke discovery for an address outside the human-approved range."""

    calls: list[DiscoveryTarget] = []

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        """Record any collector call and return a deterministic read-only result."""

        calls.append(target)
        return DiscoveryResult(target=target, state=DiscoveryState.UNREACHABLE, message="No response.")

    scope = AuthorizedScope(
        site_id="site-lab",
        approved_networks=("192.0.2.0/24",),
        allowed_protocols=(ManagementProtocol.SSH,),
        approval_reference="scope-approval-001",
    )
    target = DiscoveryTarget(address="198.51.100.10", protocol=ManagementProtocol.SSH, credential_reference="vault-ref-01")

    result = ReadOnlyDiscoveryAgent(scope, collector).discover(target)

    assert result.state is DiscoveryState.UNAUTHORIZED
    assert calls == []


def test_virtual_validation_rejects_mismatched_evidence() -> None:
    """The coordinator must reject a test result whose artifact does not match the request."""

    def mismatched_adapter(_: str, target_facts_hash: str, scope_hash: str) -> VirtualTestResult:
        """Return deliberately mismatched evidence for the guard test."""

        return VirtualTestResult(
            state=VirtualTestState.TEST_PASSED,
            adapter_kind="lab",
            fidelity_label="virtualized-image",
            artifact_hash="different-artifact",
            target_facts_hash=target_facts_hash,
            scope_hash=scope_hash,
            detail="Adapter completed its own test.",
        )

    coordinator = VirtualValidationCoordinator(mismatched_adapter)

    try:
        coordinator.validate("artifact-001", "facts-001", "scope-001")
    except ValueError as error:
        assert "artifact hash" in str(error)
    else:
        raise AssertionError("Mismatched virtual-test evidence must be rejected.")
