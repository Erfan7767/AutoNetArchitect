"""Unit tests for production-readiness boundaries."""
from __future__ import annotations

from tests.conftest import assert_production_readiness_boundaries


def test_real_execution_without_backup_is_not_ready():
    blocked = {"real_execution": True, "backup_reference": ""}
    rejected = False
    try:
        assert_production_readiness_boundaries(blocked)
    except AssertionError:
        rejected = True
    if not rejected:
        raise AssertionError("missing backup must fail the readiness boundary")


def test_dry_run_can_be_evaluated_without_production_claim():
    payload = {"real_execution": False, "status": "dry_run", "proof_status": "partially_verified"}
    assert_production_readiness_boundaries(payload) is None


def test_explicit_proof_status_is_required_when_present():
    payload = {"real_execution": False, "proof_status": "verified"}
    assert_production_readiness_boundaries(payload) is None
