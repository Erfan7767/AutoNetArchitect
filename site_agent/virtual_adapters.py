"""Vendor-aware virtual validation contracts with explicit fidelity limits."""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from .models import VirtualTestState
from .vendor_support import VendorCapabilityRegistry, VendorFamily


class VirtualFidelity(str, Enum):
    """Fidelity labels that prevent logical tests being mistaken for emulation."""

    LOGICAL_INTENT_ONLY = "logical_intent_only"
    VENDOR_IMAGE_LAB = "vendor_image_lab"
    PHYSICAL_LAB = "physical_lab"
    UNSUPPORTED = "unsupported"


class VirtualValidationPlan(BaseModel):
    """A non-executing validation plan bound to exact artifact and scope hashes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vendor_family: VendorFamily
    adapter_kind: str = Field(min_length=1, max_length=120)
    fidelity_label: VirtualFidelity
    artifact_hash: str = Field(min_length=1, max_length=160)
    target_facts_hash: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=1, max_length=160)
    evidence_requirements: tuple[str, ...] = Field(min_length=1)
    expected_state: VirtualTestState = VirtualTestState.TEST_QUEUED
    production_change_authority: bool = False
    limitation: str = Field(min_length=1, max_length=500)


class VendorVirtualValidationAdapter:
    """Contract for a vendor-specific validation path without lab execution."""

    family: ClassVar[VendorFamily]
    adapter_kind: ClassVar[str] = "logical-intent-validator"
    fidelity_label: ClassVar[VirtualFidelity] = VirtualFidelity.LOGICAL_INTENT_ONLY

    def __init__(self, registry: VendorCapabilityRegistry | None = None) -> None:
        """Bind the contract to the same vendor registry as discovery and capability checks."""

        self._registry = registry or VendorCapabilityRegistry()

    def plan(self, artifact_hash: str, target_facts_hash: str, scope_hash: str) -> VirtualValidationPlan:
        """Create a queued plan; execution and result evidence remain external and explicit."""

        if not artifact_hash.strip() or not target_facts_hash.strip() or not scope_hash.strip():
            raise ValueError("Artifact, target facts, and scope hashes are mandatory for validation scope binding.")
        contract = next((item for item in self._registry.contracts if item.family is self.family), None)
        if contract is None:
            raise LookupError(f"No vendor contract is registered for {self.family.value}.")
        return VirtualValidationPlan(
            vendor_family=self.family,
            adapter_kind=self.adapter_kind,
            fidelity_label=self.fidelity_label,
            artifact_hash=artifact_hash,
            target_facts_hash=target_facts_hash,
            scope_hash=scope_hash,
            evidence_requirements=(
                "artifact_hash_match",
                "target_facts_hash_match",
                "scope_hash_match",
                "virtual_result_record",
            ),
            limitation="Logical intent validation is not protocol emulation and cannot alone authorize production change.",
        )


class CiscoVirtualValidationAdapter(VendorVirtualValidationAdapter):
    """Cisco logical validation contract."""

    family = VendorFamily.CISCO


class HuaweiVirtualValidationAdapter(VendorVirtualValidationAdapter):
    """Huawei logical validation contract."""

    family = VendorFamily.HUAWEI


class FortinetVirtualValidationAdapter(VendorVirtualValidationAdapter):
    """Fortinet logical validation contract."""

    family = VendorFamily.FORTINET


class HpeArubaVirtualValidationAdapter(VendorVirtualValidationAdapter):
    """HPE Aruba logical validation contract."""

    family = VendorFamily.HPE_ARUBA


DEFAULT_VIRTUAL_ADAPTERS: tuple[type[VendorVirtualValidationAdapter], ...] = (
    CiscoVirtualValidationAdapter,
    HuaweiVirtualValidationAdapter,
    FortinetVirtualValidationAdapter,
    HpeArubaVirtualValidationAdapter,
)
