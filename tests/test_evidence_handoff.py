"""Tests for evidence-bound discovery-to-validation handoffs."""

import pytest

from site_agent.coordination import AgentAssignment, AgentRole
from site_agent.discovery_coordination import (
    CoordinatedDiscoveryResult,
    DiscoveryBatchResult,
)
from site_agent.evidence_handoff import DesignEvidenceHandoff, EvidenceBoundHandoffCoordinator
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, ObservedDeviceFacts, VirtualTestState
from site_agent.vendor_support import VendorFamily
from site_agent.virtual_adapters import LabValidationAdapter


def _discovered_batch() -> DiscoveryBatchResult:
    """Build a fully resolved discovery batch without contacting a device."""

    target = DiscoveryTarget(
        address="10.0.0.10",
        protocol=ManagementProtocol.HTTPS_API,
        credential_reference="credential-ref-1",
    )
    result = DiscoveryResult(
        target=target,
        state=DiscoveryState.DISCOVERED,
        facts=ObservedDeviceFacts(
            vendor="Fortinet",
            platform="FortiGate",
            software_version="8.0.0",
            serial_reference="redacted-serial-ref",
            interface_count=12,
        ),
        message="Verified through the approved read-only collector.",
    )
    return DiscoveryBatchResult(
        site_id="site-1",
        scope_hash="scope-1",
        results=(
            CoordinatedDiscoveryResult(
                assignment=AgentAssignment(
                    agent_id="agent-a",
                    role=AgentRole.AUTHORIZED_DISCOVERY,
                    site_id="site-1",
                    scope_hash="scope-1",
                    authority_reference="approval-1",
                ),
                result=result,
                scope_hash="scope-1",
            ),
        ),
    )


def _handoff(**changes: object) -> DesignEvidenceHandoff:
    """Return a complete set of opaque evidence references for test use."""

    values: dict[str, object] = {
        "site_id": "site-1",
        "scope_hash": "scope-1",
        "requirements_hash": "requirements-1",
        "design_artifact_hash": "artifact-1",
        "target_facts_hash": "facts-1",
        "discovery_evidence_reference": "discovery-run-1",
        "capability_assessment_reference": "capability-1",
    }
    values.update(changes)
    return DesignEvidenceHandoff(**values)


def test_resolved_evidence_creates_hash_bound_non_authorizing_validation_plan() -> None:
    """A fully resolved handoff produces validation evidence only, never execution authority."""

    plan = EvidenceBoundHandoffCoordinator().build_validation_plan(
        _discovered_batch(),
        _handoff(),
        LabValidationAdapter(VendorFamily.FORTINET),
    )

    assert plan.artifact_hash == "artifact-1"
    assert plan.target_facts_hash == "facts-1"
    assert plan.scope_hash == "scope-1"
    assert plan.expected_state is VirtualTestState.TEST_QUEUED
    assert plan.production_change_authority is False


@pytest.mark.parametrize(
    ("batch", "handoff", "message"),
    [
        (
            DiscoveryBatchResult(
                site_id="site-1",
                scope_hash="scope-1",
                results=(),
            ),
            _handoff(unresolved_item_ids=("capability-missing",)),
            "Unresolved design",
        ),
        (_discovered_batch(), _handoff(scope_hash="other-scope"), "not bound to the design scope"),
    ],
)
def test_unresolved_or_cross_scope_handoff_is_blocked(
    batch: DiscoveryBatchResult,
    handoff: DesignEvidenceHandoff,
    message: str,
) -> None:
    """No validation job is created when upstream evidence cannot safely support it."""

    with pytest.raises(ValueError, match=message):
        EvidenceBoundHandoffCoordinator().build_validation_plan(
            batch,
            handoff,
            LabValidationAdapter(VendorFamily.FORTINET),
        )


def test_ambiguous_discovery_result_blocks_validation_handoff() -> None:
    """A no-guess ambiguous target stays blocked rather than becoming a validation input."""

    batch = _discovered_batch().model_copy(
        update={
            "results": (
                _discovered_batch().results[0].model_copy(
                    update={
                        "result": DiscoveryResult(
                            target=_discovered_batch().results[0].result.target,
                            state=DiscoveryState.AMBIGUOUS,
                            message="Identity evidence is incomplete.",
                        ),
                    }
                ),
            ),
        }
    )

    with pytest.raises(ValueError, match="unresolved targets"):
        EvidenceBoundHandoffCoordinator().build_validation_plan(
            batch,
            _handoff(),
            LabValidationAdapter(VendorFamily.FORTINET),
        )
