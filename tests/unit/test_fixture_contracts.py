"""Unit tests for realistic fixture contracts."""
from __future__ import annotations

from tests.conftest import assert_secret_safe, load_json_fixture
from tests.final_test_helpers import SUPPORTED_VENDORS, assert_supported_vendor_set, fixture_project


def test_golden_projects_have_required_identity_and_governance_fields():
    for name in ("enterprise_greenfield", "branch_brownfield", "cross_vendor_lab"):
        project = fixture_project(name)
        for key in ("project_id", "scenario", "requirements", "governance"):
            assert key in project
        assert_secret_safe(project)


def test_cross_vendor_fixture_uses_known_vendor_families_and_explicit_preview_boundary():
    project = fixture_project("cross_vendor_lab")
    vendors = [str(device["vendor"]) for device in project["devices"]]
    assert_supported_vendor_set(vendors)
    assert "mikrotik" in project["capability_evidence"]["preview_only"]
    assert set(project["capability_evidence"]["production_path"]).issubset(set(SUPPORTED_VENDORS))


def test_expected_output_rules_are_explicit():
    expected = load_json_fixture("expected_outputs/pipeline_expectations.json")
    rules = expected["production_readiness_rules"]
    assert rules["deployment_requires_backup"] is True
    assert rules["deployment_requires_approval"] is True
    assert rules["simulation_does_not_prove_production"] is True
