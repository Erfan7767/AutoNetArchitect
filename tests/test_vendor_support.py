"""Tests for evidence-bound vendor capability assessment."""

from site_agent.models import ManagementProtocol, ObservedDeviceFacts
from site_agent.vendor_support import (
    SupportDecision,
    VendorCapabilityContract,
    VendorCapabilityRegistry,
    VendorFamily,
)


def facts(vendor: str, platform: str, capabilities: tuple[str, ...] = (), version: str = "17.13.1") -> ObservedDeviceFacts:
    """Build deterministic secret-free observed facts for a capability test."""

    return ObservedDeviceFacts(
        vendor=vendor,
        platform=platform,
        software_version=version,
        serial_reference="serial-evidence-1",
        interface_count=24,
        capabilities=capabilities,
    )


def versioned_cisco_registry() -> VendorCapabilityRegistry:
    """Return a test-only Cisco contract whose version boundary is explicit."""

    contract = VendorCapabilityContract(
        family=VendorFamily.CISCO,
        vendor_markers=("cisco",),
        platform_markers=("ios xe",),
        supported_version_prefixes=("17.13.",),
        protocols=(ManagementProtocol.NETCONF,),
        source_url="https://example.invalid/evidence/cisco-ios-xe-17.13",
    )
    return VendorCapabilityRegistry((contract,))


def test_supported_identity_without_license_requires_review() -> None:
    """Known identity and protocol do not permit configuration without entitlement evidence."""

    assessment = versioned_cisco_registry().assess(
        facts("Cisco Systems", "Cisco IOS XE"),
        ManagementProtocol.NETCONF,
    )

    assert assessment.decision is SupportDecision.REVIEW_REQUIRED
    assert assessment.production_configuration_allowed is False
    assert "license_evidence" in assessment.required_evidence


def test_configuration_support_requires_verified_path_and_license() -> None:
    """Configuration support is granted only when all explicit evidence gates are present."""

    observed = facts("Cisco Systems", "Cisco IOS XE", ("configuration_path_verified", "bgp"))
    assessment = versioned_cisco_registry().assess(
        observed,
        ManagementProtocol.NETCONF,
        license_evidence=True,
        requested_capabilities=("bgp",),
    )

    assert assessment.decision is SupportDecision.CONFIGURATION_SUPPORTED
    assert assessment.production_configuration_allowed is True


def test_unknown_vendor_is_unsupported() -> None:
    """An unknown vendor is never mapped to a known vendor contract."""

    assessment = VendorCapabilityRegistry().assess(facts("Unknown Vendor", "Unknown OS"), ManagementProtocol.SSH)

    assert assessment.decision is SupportDecision.UNSUPPORTED
    assert assessment.vendor_family is None


def test_known_vendor_with_unmatched_platform_requires_review() -> None:
    """A known vendor with an unrecognized platform is ambiguous rather than guessed."""

    assessment = VendorCapabilityRegistry().assess(facts("Fortinet", "Unidentified Platform"), ManagementProtocol.HTTPS_API)

    assert assessment.decision is SupportDecision.REVIEW_REQUIRED
    assert "exact_platform_evidence" in assessment.required_evidence


def test_protocol_outside_contract_is_unsupported() -> None:
    """An unsupported management protocol is blocked even when the vendor is known."""

    assessment = VendorCapabilityRegistry().assess(facts("HPE Aruba", "AOS-CX"), ManagementProtocol.SNMP)

    assert assessment.decision is SupportDecision.UNSUPPORTED
    assert assessment.production_configuration_allowed is False


def test_missing_requested_capability_requires_review() -> None:
    """A requested feature without observed evidence cannot become a configuration recommendation."""

    assessment = versioned_cisco_registry().assess(
        facts("Cisco", "IOS XE", ("configuration_path_verified",)),
        ManagementProtocol.NETCONF,
        license_evidence=True,
        requested_capabilities=("multicast",),
    )

    assert assessment.decision is SupportDecision.REVIEW_REQUIRED
    assert assessment.required_evidence == ("multicast",)


def test_mismatched_version_is_unsupported() -> None:
    """A version outside the explicit contract boundary is blocked rather than guessed."""

    assessment = versioned_cisco_registry().assess(
        facts("Cisco", "IOS XE", version="16.12.10"),
        ManagementProtocol.NETCONF,
        license_evidence=True,
    )

    assert assessment.decision is SupportDecision.UNSUPPORTED
    assert "supported_software_version" in assessment.required_evidence
