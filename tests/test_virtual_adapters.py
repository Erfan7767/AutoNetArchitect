"""Tests for vendor-aware virtual validation contracts."""

import pytest

from site_agent.models import VirtualTestState
from site_agent.vendor_support import VendorFamily
from site_agent.virtual_adapters import (
    CandidateCommitValidationAdapter,
    CiscoVirtualValidationAdapter,
    DigitalTwinValidationAdapter,
    FortinetVirtualValidationAdapter,
    HpeArubaVirtualValidationAdapter,
    HuaweiVirtualValidationAdapter,
    LabValidationAdapter,
    VirtualFidelity,
    VirtualValidationPath,
)


@pytest.mark.parametrize(
    "adapter_type",
    (
        CiscoVirtualValidationAdapter,
        HuaweiVirtualValidationAdapter,
        FortinetVirtualValidationAdapter,
        HpeArubaVirtualValidationAdapter,
    ),
)
def test_vendor_virtual_plan_is_scope_bound_and_non_authorizing(adapter_type: type) -> None:
    """Each vendor plan binds all hashes and cannot authorize a production change."""

    plan = adapter_type().plan("artifact-1", "facts-1", "scope-1")

    assert plan.fidelity_label is VirtualFidelity.LOGICAL_INTENT_ONLY
    assert plan.expected_state is VirtualTestState.TEST_QUEUED
    assert plan.artifact_hash == "artifact-1"
    assert plan.target_facts_hash == "facts-1"
    assert plan.scope_hash == "scope-1"
    assert plan.production_change_authority is False
    assert "not protocol emulation" in plan.limitation


def test_virtual_plan_requires_all_scope_hashes() -> None:
    """A validation plan cannot be created without artifact, facts, and scope identity."""

    with pytest.raises(ValueError, match="hashes are mandatory"):
        CiscoVirtualValidationAdapter().plan("artifact-1", "", "scope-1")


@pytest.mark.parametrize(
    ("adapter_type", "path", "fidelity"),
    (
        (LabValidationAdapter, VirtualValidationPath.LAB, VirtualFidelity.VENDOR_IMAGE_LAB),
        (DigitalTwinValidationAdapter, VirtualValidationPath.DIGITAL_TWIN, VirtualFidelity.LOGICAL_INTENT_ONLY),
        (CandidateCommitValidationAdapter, VirtualValidationPath.VENDOR_CANDIDATE_COMMIT, VirtualFidelity.CANDIDATE_COMMIT_EVIDENCE),
    ),
)
def test_explicit_validation_paths_are_scope_bound_and_non_authorizing(adapter_type: type, path: VirtualValidationPath, fidelity: VirtualFidelity) -> None:
    """Each distinct path has a declared fidelity and never grants production authority."""

    plan = adapter_type(VendorFamily.CISCO).plan("artifact-2", "facts-2", "scope-2")

    assert plan.validation_path is path
    assert plan.fidelity_label is fidelity
    assert plan.artifact_hash == "artifact-2"
    assert plan.target_facts_hash == "facts-2"
    assert plan.scope_hash == "scope-2"
    assert plan.production_change_authority is False


def test_path_contract_rejects_missing_scope_identity() -> None:
    """No path can be created without all immutable identity hashes."""

    with pytest.raises(ValueError, match="hashes are mandatory"):
        LabValidationAdapter(VendorFamily.HPE_ARUBA).plan("artifact-2", "facts-2", "")
