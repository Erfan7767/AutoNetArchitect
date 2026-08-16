"""Tests for vendor-aware virtual validation contracts."""

import pytest

from site_agent.models import VirtualTestState
from site_agent.virtual_adapters import (
    CiscoVirtualValidationAdapter,
    FortinetVirtualValidationAdapter,
    HpeArubaVirtualValidationAdapter,
    HuaweiVirtualValidationAdapter,
    VirtualFidelity,
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
