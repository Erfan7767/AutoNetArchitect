"""Tests for exact platform/version/license capability assessment."""

import pytest

from site_agent.exact_capability import ExactCapabilityAssessor, ExactCapabilityEvidence
from site_agent.models import ManagementProtocol, ObservedDeviceFacts
from site_agent.vendor_support import SupportDecision, VendorFamily


def _cisco_facts() -> ObservedDeviceFacts:
    """Return observed Cisco facts with only explicitly provided capability evidence."""

    return ObservedDeviceFacts(
        vendor="Cisco Systems",
        platform="Catalyst 9300 IOS XE",
        software_version="17.18.1",
        serial_reference="redacted-serial-reference",
        interface_count=24,
        capabilities=("routing",),
    )


def test_candidate_release_never_becomes_configuration_authority_without_exact_policy() -> None:
    """A reviewed release-note candidate remains review-required, not supported by assumption."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=_cisco_facts(),
            protocol=ManagementProtocol.NETCONF,
            platform_family="catalyst",
            exact_model_evidence_reference="observed-model-evidence-1",
            license_evidence_reference="entitlement-record-1",
            configuration_path_evidence_reference="path-evidence-1",
            requested_capabilities=("routing",),
        )
    )

    assert result.vendor_family is VendorFamily.CISCO
    assert result.decision is SupportDecision.REVIEW_REQUIRED
    assert result.production_configuration_allowed is False
    assert "Release-note candidate" in result.reason


def test_missing_exact_model_evidence_blocks_version_and_license_assumptions() -> None:
    """A platform string is not accepted as an exact model entitlement record."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=_cisco_facts(),
            protocol=ManagementProtocol.NETCONF,
            platform_family="catalyst",
        )
    )

    assert result.decision is SupportDecision.REVIEW_REQUIRED
    assert result.required_evidence == ("exact_model_evidence",)


def test_unverified_license_follows_explicit_blocked_policy() -> None:
    """Exact device facts cannot bypass a policy entry that blocks unverified entitlement."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=_cisco_facts(),
            protocol=ManagementProtocol.NETCONF,
            platform_family="catalyst",
            exact_model_evidence_reference="observed-model-evidence-1",
        )
    )

    assert result.decision is SupportDecision.UNSUPPORTED
    assert result.production_configuration_allowed is False
    assert result.required_evidence == ("license_evidence",)


def test_unobserved_requested_capability_stays_review_required() -> None:
    """The assessor returns missing capability evidence instead of filling it from policy text."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=_cisco_facts(),
            protocol=ManagementProtocol.NETCONF,
            platform_family="catalyst",
            exact_model_evidence_reference="observed-model-evidence-1",
            requested_capabilities=("routing", "multicast"),
        )
    )

    assert result.decision is SupportDecision.REVIEW_REQUIRED
    assert result.required_evidence == ("multicast",)


@pytest.mark.parametrize(
    ("facts", "platform_family", "protocol", "family"),
    [
        (_cisco_facts(), "catalyst", ManagementProtocol.NETCONF, VendorFamily.CISCO),
        (
            ObservedDeviceFacts(
                vendor="Huawei",
                platform="CloudEngine VRP",
                software_version="V800R022C00SPC500",
                serial_reference="redacted-huawei-serial",
                interface_count=48,
            ),
            "vrp",
            ManagementProtocol.NETCONF,
            VendorFamily.HUAWEI,
        ),
        (
            ObservedDeviceFacts(
                vendor="Fortinet",
                platform="FortiGate FortiOS",
                software_version="8.0.0",
                serial_reference="redacted-fortinet-serial",
                interface_count=12,
            ),
            "fortigate",
            ManagementProtocol.HTTPS_API,
            VendorFamily.FORTINET,
        ),
        (
            ObservedDeviceFacts(
                vendor="HPE Aruba",
                platform="AOS-CX",
                software_version="10.14.0",
                serial_reference="redacted-aruba-serial",
                interface_count=24,
            ),
            "aos_cx",
            ManagementProtocol.HTTPS_API,
            VendorFamily.HPE_ARUBA,
        ),
    ],
)
def test_all_four_vendor_families_block_unverified_license_before_handoff(
    facts: ObservedDeviceFacts,
    platform_family: str,
    protocol: ManagementProtocol,
    family: VendorFamily,
) -> None:
    """Candidate release evidence and a model reference cannot replace entitlement verification."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=facts,
            protocol=protocol,
            platform_family=platform_family,
            exact_model_evidence_reference="observed-model-evidence",
        )
    )

    assert result.vendor_family is family
    assert result.decision is SupportDecision.UNSUPPORTED
    assert result.production_configuration_allowed is False
    assert result.required_evidence == ("license_evidence",)


@pytest.mark.parametrize(
    ("facts", "platform_family", "protocol"),
    [
        (_cisco_facts(), "catalyst", ManagementProtocol.NETCONF),
        (
            ObservedDeviceFacts(
                vendor="Huawei",
                platform="CloudEngine VRP",
                software_version="V800R022C00SPC500",
                serial_reference="redacted-huawei-serial",
                interface_count=48,
            ),
            "vrp",
            ManagementProtocol.NETCONF,
        ),
        (
            ObservedDeviceFacts(
                vendor="Fortinet",
                platform="FortiGate FortiOS",
                software_version="8.0.0",
                serial_reference="redacted-fortinet-serial",
                interface_count=12,
            ),
            "fortigate",
            ManagementProtocol.HTTPS_API,
        ),
        (
            ObservedDeviceFacts(
                vendor="HPE Aruba",
                platform="AOS-CX",
                software_version="10.14.0",
                serial_reference="redacted-aruba-serial",
                interface_count=24,
            ),
            "aos_cx",
            ManagementProtocol.HTTPS_API,
        ),
    ],
)
def test_all_four_vendor_candidates_remain_review_required_with_references(
    facts: ObservedDeviceFacts,
    platform_family: str,
    protocol: ManagementProtocol,
) -> None:
    """A release-note candidate still cannot be used as an exact platform/configuration approval."""

    result = ExactCapabilityAssessor().assess(
        ExactCapabilityEvidence(
            facts=facts,
            protocol=protocol,
            platform_family=platform_family,
            exact_model_evidence_reference="observed-model-evidence",
            license_evidence_reference="entitlement-evidence",
            configuration_path_evidence_reference="configuration-path-evidence",
        )
    )

    assert result.decision is SupportDecision.REVIEW_REQUIRED
    assert result.production_configuration_allowed is False
    assert "Release-note candidate" in result.reason
