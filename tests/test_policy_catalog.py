"""Tests for evidence-bound vendor policy evaluation."""

from pathlib import Path

from site_agent.policy_catalog import VendorPolicyCatalog


POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "vendor_support_policy.json"


def test_candidate_release_requires_review_and_does_not_authorize_configuration() -> None:
    """A Cisco release-note candidate cannot bypass exact device evidence."""

    decision = VendorPolicyCatalog(POLICY_PATH).assess("cisco", "catalyst", "17.18.1", True, True)

    assert decision.decision == "review_required"
    assert not decision.configuration_allowed
    assert "exact_model_evidence" in decision.required_evidence
    assert decision.source_urls


def test_version_outside_policy_is_unsupported() -> None:
    """A version not present in supported or candidate policy is not guessed."""

    decision = VendorPolicyCatalog(POLICY_PATH).assess("fortinet", "fortigate", "6.4.0", True, True)

    assert decision.decision == "unsupported"
    assert not decision.configuration_allowed
    assert "supported_software_version" in decision.required_evidence


def test_loaded_supported_prefix_would_still_require_license_and_path_evidence(tmp_path: Path) -> None:
    """Even a reviewed exact prefix cannot authorize without entitlement and path evidence."""

    policy = {
        "schema_version": 2,
        "policy_state": "evidence_required",
        "vendors": [
            {
                "vendor_family": "cisco",
                "platform_families": ["catalyst"],
                "supported_version_prefixes": ["17.18"],
                "reviewed_candidate_releases": [],
                "license_evidence_required": True,
                "configuration_path_evidence_required": True,
                "status": "verification_required",
            }
        ],
    }
    path = tmp_path / "policy.json"
    path.write_text(__import__("json").dumps(policy), encoding="utf-8")

    decision = VendorPolicyCatalog(path).assess("cisco", "catalyst", "17.18.1", False, False)

    assert decision.decision == "review_required"
    assert decision.required_evidence == ("license_evidence", "configuration_path_evidence")
    assert not decision.configuration_allowed


def test_real_policy_covers_version_and_license_decisions_for_all_four_families() -> None:
    """Every loaded family refuses unverified release or entitlement evidence."""

    catalog = VendorPolicyCatalog(POLICY_PATH)
    cases = (
        ("cisco", "catalyst"),
        ("huawei", "vrp"),
        ("fortinet", "fortigate"),
        ("hpe_aruba", "aos_cx"),
    )
    for vendor_family, platform_family in cases:
        out_of_policy = catalog.assess(vendor_family, platform_family, "0.0.0", True, True)
        assert out_of_policy.decision == "unsupported"
        assert not out_of_policy.configuration_allowed
        missing_license = catalog.assess(vendor_family, platform_family, "1.0.0", False, True)
        assert missing_license.decision in {"blocked", "review_required", "unsupported"}
        assert not missing_license.configuration_allowed
