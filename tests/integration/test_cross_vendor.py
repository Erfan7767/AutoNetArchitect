"""Integration tests for cross-vendor capability boundaries."""
from __future__ import annotations

from tests.final_test_helpers import assert_supported_vendor_set, fixture_project


def test_cross_vendor_fixture_covers_supported_families():
    project = fixture_project("cross_vendor_lab")
    vendors = [str(device["vendor"]) for device in project["devices"]]
    assert_supported_vendor_set(vendors)
    assert len(set(vendors)) >= 5


def test_preview_only_vendor_cannot_enter_production_path():
    project = fixture_project("cross_vendor_lab")
    preview = set(project["capability_evidence"]["preview_only"])
    production = set(project["capability_evidence"]["production_path"])
    assert preview.isdisjoint(production)
    assert project["capability_evidence"]["unsupported_feature_policy"] == "record-and-block"


def test_cross_vendor_safety_constraints_are_explicit():
    constraints = fixture_project("cross_vendor_lab")["expected_constraints"]
    assert constraints["no_fake_asn"] is True
    assert constraints["no_fake_public_prefix"] is True
    assert constraints["no_secret_values_in_artifacts"] is True
    assert constraints["lab_is_not_production_change_control"] is True
