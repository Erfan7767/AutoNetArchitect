"""Evidence-bound vendor capability contracts for the local agent."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from .models import ManagementProtocol, ObservedDeviceFacts


class VendorFamily(str, Enum):
    """Vendor families covered by the initial support boundary."""

    CISCO = "cisco"
    HUAWEI = "huawei"
    FORTINET = "fortinet"
    HPE_ARUBA = "hpe_aruba"


class SupportDecision(str, Enum):
    """Decision produced by capability assessment without creating commands."""

    DISCOVERY_SUPPORTED = "discovery_supported"
    CONFIGURATION_SUPPORTED = "configuration_supported"
    REVIEW_REQUIRED = "review_required"
    UNSUPPORTED = "unsupported"


class CapabilityAssessment(BaseModel):
    """Secret-free result of a vendor capability assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vendor_family: VendorFamily | None = None
    decision: SupportDecision
    reason: str = Field(min_length=1, max_length=600)
    source_url: str | None = None
    production_configuration_allowed: bool = False
    required_evidence: tuple[str, ...] = ()


class VendorCapabilityContract(BaseModel):
    """Observed-identity and exact-version contract for one vendor family."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    family: VendorFamily
    vendor_markers: tuple[str, ...] = Field(min_length=1)
    platform_markers: tuple[str, ...] = Field(min_length=1)
    supported_version_prefixes: tuple[str, ...] = ()
    protocols: tuple[ManagementProtocol, ...] = Field(min_length=1)
    source_url: str

    def matches_vendor(self, vendor: str) -> bool:
        """Return whether the observed vendor string matches this contract."""

        normalized = vendor.casefold()
        return any(marker.casefold() in normalized for marker in self.vendor_markers)

    def matches_platform(self, platform: str) -> bool:
        """Return whether the observed platform matches a declared platform marker."""

        normalized = platform.casefold()
        return any(marker.casefold() in normalized for marker in self.platform_markers)

    def matches_version(self, software_version: str) -> bool:
        """Return whether the observed software version is within the declared policy."""

        return bool(self.supported_version_prefixes) and any(
            software_version.casefold().startswith(prefix.casefold()) for prefix in self.supported_version_prefixes
        )

    def assess(
        self,
        facts: ObservedDeviceFacts,
        protocol: ManagementProtocol,
        license_evidence: bool = False,
        requested_capabilities: Iterable[str] = (),
    ) -> CapabilityAssessment:
        """Assess observed facts without synthesizing any device command."""

        required = tuple(sorted(set(requested_capabilities)))
        if not self.matches_vendor(facts.vendor):
            return CapabilityAssessment(
                decision=SupportDecision.UNSUPPORTED,
                reason="Observed vendor is outside this contract.",
                required_evidence=("vendor_family_evidence",),
            )
        if not self.matches_platform(facts.platform):
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="Vendor matches, but the observed platform is not in the declared boundary.",
                source_url=self.source_url,
                required_evidence=("exact_platform_evidence", "exact_software_version_evidence"),
            )
        if protocol not in self.protocols:
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.UNSUPPORTED,
                reason="The requested management protocol is not declared for this contract.",
                source_url=self.source_url,
                required_evidence=("protocol_support_evidence",),
            )
        if not facts.software_version.strip() or not facts.serial_reference.strip():
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="Exact software version and serial reference evidence are required.",
                source_url=self.source_url,
                required_evidence=("exact_software_version_evidence", "device_identity_evidence"),
            )
        if not self.supported_version_prefixes:
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="No exact version policy is loaded for this vendor and platform path.",
                source_url=self.source_url,
                required_evidence=("vendor_version_policy",),
            )
        if not self.matches_version(facts.software_version):
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.UNSUPPORTED,
                reason="Observed software version is outside the declared support boundary.",
                source_url=self.source_url,
                required_evidence=("supported_software_version",),
            )
        observed_capabilities = set(facts.capabilities)
        missing = tuple(item for item in required if item not in observed_capabilities)
        if missing:
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="Requested capabilities are not proven by the observed evidence.",
                source_url=self.source_url,
                required_evidence=missing,
            )
        if not license_evidence:
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="A current license or entitlement record is required before configuration support.",
                source_url=self.source_url,
                required_evidence=("license_evidence", "configuration_path_evidence"),
            )
        if "configuration_path_verified" not in observed_capabilities:
            return CapabilityAssessment(
                vendor_family=self.family,
                decision=SupportDecision.REVIEW_REQUIRED,
                reason="The exact configuration path is not verified for this device evidence set.",
                source_url=self.source_url,
                required_evidence=("configuration_path_evidence",),
            )
        return CapabilityAssessment(
            vendor_family=self.family,
            decision=SupportDecision.CONFIGURATION_SUPPORTED,
            reason="Identity, platform, version, protocol, license, and configuration-path evidence are present.",
            source_url=self.source_url,
            production_configuration_allowed=True,
        )


class VendorCapabilityRegistry:
    """Registry that selects a contract from observed facts without guessing."""

    def __init__(self, contracts: tuple[VendorCapabilityContract, ...] | None = None) -> None:
        """Create a registry with the bounded initial vendor contracts."""

        self._contracts = contracts or self.default_contracts()

    @property
    def contracts(self) -> tuple[VendorCapabilityContract, ...]:
        """Return the immutable contract set exposed to adapter integrations."""

        return self._contracts

    @staticmethod
    def default_contracts() -> tuple[VendorCapabilityContract, ...]:
        """Return the four documented contracts with no unverified version claims loaded."""

        return (
            VendorCapabilityContract(
                family=VendorFamily.CISCO,
                vendor_markers=("cisco",),
                platform_markers=("ios xe", "catalyst", "nexus", "nx-os"),
                protocols=(ManagementProtocol.NETCONF, ManagementProtocol.HTTPS_API, ManagementProtocol.SSH),
                source_url="https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1713/b_1713_programmability_cg/m_1713_prog_yang_netconf.html",
            ),
            VendorCapabilityContract(
                family=VendorFamily.HUAWEI,
                vendor_markers=("huawei",),
                platform_markers=("vrp", "cloudengine"),
                protocols=(ManagementProtocol.NETCONF, ManagementProtocol.HTTPS_API, ManagementProtocol.SSH),
                source_url="https://support.huawei.com/enterprise/en/doc/EDOC1100278266/d73bfdce/overview-of-restconf",
            ),
            VendorCapabilityContract(
                family=VendorFamily.FORTINET,
                vendor_markers=("fortinet", "fortigate"),
                platform_markers=("fortios", "fortigate"),
                protocols=(ManagementProtocol.HTTPS_API, ManagementProtocol.SSH),
                source_url="https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/940602/using-apis",
            ),
            VendorCapabilityContract(
                family=VendorFamily.HPE_ARUBA,
                vendor_markers=("aruba", "hpe"),
                platform_markers=("aos-cx", "aruba cx"),
                protocols=(ManagementProtocol.HTTPS_API, ManagementProtocol.SSH),
                source_url="https://developer.arubanetworks.com/aoscx/docs/introduction",
            ),
        )

    def contract_for(self, facts: ObservedDeviceFacts) -> VendorCapabilityContract | None:
        """Return the matching vendor contract, or no contract when identity is unknown."""

        for contract in self._contracts:
            if contract.matches_vendor(facts.vendor):
                return contract
        return None

    def assess(
        self,
        facts: ObservedDeviceFacts,
        protocol: ManagementProtocol,
        license_evidence: bool = False,
        requested_capabilities: Iterable[str] = (),
    ) -> CapabilityAssessment:
        """Assess observed facts against one matching contract or return unsupported."""

        contract = self.contract_for(facts)
        if contract is not None:
            return contract.assess(facts, protocol, license_evidence, requested_capabilities)
        return CapabilityAssessment(
            decision=SupportDecision.UNSUPPORTED,
            reason="Observed vendor is not in the initial support boundary.",
            required_evidence=("supported_vendor_family_evidence",),
        )
