"""Tests for traceable, non-authorizing vendor release policy data."""

from __future__ import annotations

import json
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "vendor_support_policy.json"


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_candidate_release_records_are_traceable_but_do_not_authorize_configuration() -> None:
    """Release-note evidence is recorded without silently becoming a support matrix."""

    policy = _policy()
    vendors = policy["vendors"]
    assert isinstance(vendors, list)
    assert {item["vendor_family"] for item in vendors} == {"cisco", "huawei", "fortinet", "hpe_aruba"}
    assert all(item["supported_version_prefixes"] == [] for item in vendors)
    assert all(item["status"] == "verification_required" for item in vendors)
    for item in vendors:
        candidates = item.get("reviewed_candidate_releases", [])
        assert candidates
        for candidate in candidates:
            assert candidate["release_prefix"]
            assert candidate["source_url"].startswith("https://")
            assert candidate["decision"] == "verification_required"


def test_policy_keeps_license_and_configuration_path_evidence_mandatory() -> None:
    """Candidate release notes cannot bypass entitlement or exact configuration-path evidence."""

    vendors = _policy()["vendors"]
    assert all(item["license_evidence_required"] for item in vendors)
    assert all(item["configuration_path_evidence_required"] for item in vendors)


def test_each_vendor_has_explicit_out_of_bound_license_boundary() -> None:
    """Every family records a concrete blocked boundary for unverified entitlement."""

    vendors = _policy()["vendors"]
    for item in vendors:
        entries = item["reviewed_out_of_bound_entries"]
        assert entries
        assert any(entry["license_state"] == "unverified" and entry["decision"] == "blocked" for entry in entries)
        assert all(entry["source_url"].startswith("https://") for entry in entries)
