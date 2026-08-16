"""Vendor discovery plans that describe evidence collection without executing commands."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from .models import DiscoveryTarget, ManagementProtocol
from .vendor_support import VendorCapabilityContract, VendorCapabilityRegistry, VendorFamily


class ReadOnlyRequest(BaseModel):
    """A vendor-neutral description of an approved read-only evidence request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: str = Field(min_length=1, max_length=120)
    protocol: ManagementProtocol
    read_only: bool = True
    required_evidence: tuple[str, ...] = Field(min_length=1)
    credential_reference: str = Field(min_length=1, max_length=160)


class DiscoveryPlan(BaseModel):
    """Secret-free discovery plan bound to one target and vendor contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vendor_family: VendorFamily
    target: DiscoveryTarget
    requests: tuple[ReadOnlyRequest, ...] = Field(min_length=1)
    source_url: str
    execution_mode: str = "read_only_only"


class VendorDiscoveryAdapter:
    """Base contract for a vendor-specific read-only discovery plan."""

    family: ClassVar[VendorFamily]
    operations: ClassVar[tuple[str, ...]] = (
        "identity",
        "software_version",
        "interfaces_summary",
        "capabilities",
    )

    def __init__(self, registry: VendorCapabilityRegistry | None = None) -> None:
        """Bind the adapter to the capability registry used for scope decisions."""

        self._registry = registry or VendorCapabilityRegistry()

    def contract(self) -> VendorCapabilityContract:
        """Return this adapter's contract, refusing accidental cross-family use."""

        for contract in self._registry.contracts:
            if contract.family is self.family:
                return contract
        raise LookupError(f"No capability contract is registered for {self.family.value}.")

    def plan(self, target: DiscoveryTarget) -> DiscoveryPlan:
        """Create read-only evidence requests without producing device commands."""

        contract = self.contract()
        if target.protocol not in contract.protocols:
            raise ValueError(f"Protocol {target.protocol.value} is not supported by {self.family.value} discovery.")
        requests = tuple(
            ReadOnlyRequest(
                operation=operation,
                protocol=target.protocol,
                required_evidence=(self.evidence_key(operation),),
                credential_reference=target.credential_reference,
            )
            for operation in self.operations
        )
        return DiscoveryPlan(
            vendor_family=self.family,
            target=target,
            requests=requests,
            source_url=contract.source_url,
        )

    @staticmethod
    def evidence_key(operation: str) -> str:
        """Map a plan operation to a stable evidence key."""

        return f"discovery.{operation}"


class CiscoDiscoveryAdapter(VendorDiscoveryAdapter):
    """Read-only discovery contract for Cisco IOS XE, Catalyst, and Nexus paths."""

    family = VendorFamily.CISCO


class HuaweiDiscoveryAdapter(VendorDiscoveryAdapter):
    """Read-only discovery contract for Huawei VRP and CloudEngine paths."""

    family = VendorFamily.HUAWEI


class FortinetDiscoveryAdapter(VendorDiscoveryAdapter):
    """Read-only discovery contract for FortiOS/FortiGate paths."""

    family = VendorFamily.FORTINET

    operations = (
        "identity",
        "software_version",
        "interfaces_summary",
        "capabilities",
        "virtual_domains_summary",
    )


class HpeArubaDiscoveryAdapter(VendorDiscoveryAdapter):
    """Read-only discovery contract for HPE Aruba AOS-CX paths."""

    family = VendorFamily.HPE_ARUBA


DEFAULT_DISCOVERY_ADAPTERS: tuple[type[VendorDiscoveryAdapter], ...] = (
    CiscoDiscoveryAdapter,
    HuaweiDiscoveryAdapter,
    FortinetDiscoveryAdapter,
    HpeArubaDiscoveryAdapter,
)
