"""Traceable vendor release-policy evaluation without command generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PolicyDecision:
    """Secret-free policy result for one vendor/platform/version evidence set."""

    vendor_family: str
    decision: str
    reason: str
    source_urls: tuple[str, ...]
    required_evidence: tuple[str, ...]
    configuration_allowed: bool = False


class VendorPolicyCatalog:
    """Loads reviewed policy data and never treats candidate release notes as approval."""

    def __init__(self, policy_path: Path) -> None:
        """Load and validate the version policy document from a controlled path."""

        payload = json.loads(policy_path.read_text(encoding="utf-8"))
        if payload.get("policy_state") != "evidence_required":
            raise ValueError("Vendor policy must remain in evidence_required state.")
        vendors = payload.get("vendors")
        if not isinstance(vendors, list) or not vendors:
            raise ValueError("Vendor policy must contain a non-empty vendors list.")
        self._vendors: dict[str, dict[str, Any]] = {str(item["vendor_family"]): item for item in vendors}

    def assess(
        self,
        vendor_family: str,
        platform_family: str,
        software_version: str,
        license_evidence: bool,
        configuration_path_evidence: bool,
    ) -> PolicyDecision:
        """Return a bounded decision for exact evidence without fabricating compatibility."""

        entry = self._vendors.get(vendor_family)
        if entry is None:
            return PolicyDecision(vendor_family, "unsupported", "Vendor family is outside the loaded policy.", (), ("vendor_policy_entry",))
        platform_families = {str(value).casefold() for value in entry.get("platform_families", [])}
        if platform_family.casefold() not in platform_families:
            return PolicyDecision(
                vendor_family,
                "review_required",
                "Platform family is not in the loaded vendor policy boundary.",
                _source_urls(entry),
                ("exact_platform_policy",),
            )
        version = software_version.strip().casefold()
        supported_prefixes = tuple(str(value).casefold() for value in entry.get("supported_version_prefixes", []))
        candidate_prefixes = tuple(
            str(item.get("release_prefix", "")).casefold() for item in entry.get("reviewed_candidate_releases", [])
        )
        if not version:
            return PolicyDecision(vendor_family, "review_required", "Exact software version is required.", _source_urls(entry), ("exact_software_version",))
        if not license_evidence:
            blocked_entry = next(
                (
                    item
                    for item in entry.get("reviewed_out_of_bound_entries", [])
                    if str(item.get("platform_family", "")).casefold() == platform_family.casefold()
                    and str(item.get("license_state", "")).casefold() == "unverified"
                ),
                None,
            )
            if blocked_entry is not None:
                return PolicyDecision(
                    vendor_family,
                    "blocked",
                    str(blocked_entry.get("reason", "Unverified entitlement is explicitly blocked by policy.")),
                    _source_urls(entry),
                    ("license_evidence",),
                )
        if not any(version.startswith(prefix) for prefix in supported_prefixes if prefix):
            if any(version.startswith(prefix) for prefix in candidate_prefixes if prefix):
                return PolicyDecision(
                    vendor_family,
                    "review_required",
                    "Release-note candidate is present, but exact model, feature, entitlement, and path evidence are not an approval.",
                    _source_urls(entry),
                    ("exact_model_evidence", "feature_evidence", "license_evidence", "configuration_path_evidence"),
                )
            return PolicyDecision(
                vendor_family,
                "unsupported",
                "Software version is outside the loaded supported-version prefixes.",
                _source_urls(entry),
                ("supported_software_version",),
            )
        required: list[str] = []
        if not license_evidence:
            required.append("license_evidence")
        if not configuration_path_evidence:
            required.append("configuration_path_evidence")
        if required:
            return PolicyDecision(vendor_family, "review_required", "Required entitlement or configuration-path evidence is missing.", _source_urls(entry), tuple(required))
        return PolicyDecision(vendor_family, "configuration_supported", "Exact policy prefix and required evidence are present.", _source_urls(entry), (), True)


def _source_urls(entry: dict[str, Any]) -> tuple[str, ...]:
    """Collect unique HTTPS sources from a policy entry."""

    urls: list[str] = []
    for item in (*entry.get("reviewed_candidate_releases", []), *entry.get("reviewed_out_of_bound_entries", [])):
        source_url = str(item.get("source_url", ""))
        if source_url.startswith("https://") and source_url not in urls:
            urls.append(source_url)
    return tuple(urls)
