"""Pure vendor-support presentation helpers for the Windows application."""

from __future__ import annotations

from dataclasses import dataclass

from site_agent.models import ManagementProtocol
from site_agent.vendor_support import VendorCapabilityContract, VendorCapabilityRegistry


@dataclass(frozen=True)
class VendorSupportRow:
    """Secret-free row shown by the local vendor-support review surface."""

    vendor_family: str
    protocols: tuple[str, ...]
    configuration_status: str
    version_policy_status: str
    boundary: str


def contracts_for_display(registry: VendorCapabilityRegistry | None = None) -> tuple[VendorCapabilityContract, ...]:
    """Return the immutable vendor contracts available to the local UI."""

    return (registry or VendorCapabilityRegistry()).contracts


def support_rows(registry: VendorCapabilityRegistry | None = None) -> tuple[VendorSupportRow, ...]:
    """Build rows without exposing credentials or creating any connection request."""

    rows: list[VendorSupportRow] = []
    for contract in contracts_for_display(registry):
        rows.append(
            VendorSupportRow(
                vendor_family=contract.family.value,
                protocols=tuple(protocol.value for protocol in contract.protocols),
                configuration_status="verification_required",
                version_policy_status="not_loaded" if not contract.supported_version_prefixes else "loaded",
                boundary="Exact platform, version, license, and configuration-path evidence is required.",
            )
        )
    return tuple(rows)


def protocol_allowed(vendor_family: str, protocol: ManagementProtocol, registry: VendorCapabilityRegistry | None = None) -> bool:
    """Return whether a selected vendor family declares the selected read-only protocol."""

    contract = next((item for item in contracts_for_display(registry) if item.family.value == vendor_family), None)
    return contract is not None and protocol in contract.protocols
