"""Secure on-premises foundations for the AutoNetArchitect site agent."""

from .agent import ReadOnlyDiscoveryAgent
from .discovery_adapters import (
    CiscoDiscoveryAdapter,
    DiscoveryPlan,
    FortinetDiscoveryAdapter,
    HpeArubaDiscoveryAdapter,
    HuaweiDiscoveryAdapter,
    ReadOnlyRequest,
)
from .models import AgentHealth, DiscoveryResult, DiscoveryTarget, VirtualTestResult
from .scope import AuthorizedScope
from .virtual_adapters import (
    CiscoVirtualValidationAdapter,
    FortinetVirtualValidationAdapter,
    HpeArubaVirtualValidationAdapter,
    HuaweiVirtualValidationAdapter,
    VirtualFidelity,
    VirtualValidationPlan,
)
from .virtual_validation import VirtualValidationCoordinator
from .vendor_support import CapabilityAssessment, SupportDecision, VendorCapabilityContract, VendorCapabilityRegistry, VendorFamily

__all__ = [
    "AgentHealth",
    "AuthorizedScope",
    "DiscoveryResult",
    "DiscoveryTarget",
    "ReadOnlyDiscoveryAgent",
    "ReadOnlyRequest",
    "DiscoveryPlan",
    "CiscoDiscoveryAdapter",
    "HuaweiDiscoveryAdapter",
    "FortinetDiscoveryAdapter",
    "HpeArubaDiscoveryAdapter",
    "VirtualTestResult",
    "VirtualFidelity",
    "VirtualValidationPlan",
    "CiscoVirtualValidationAdapter",
    "HuaweiVirtualValidationAdapter",
    "FortinetVirtualValidationAdapter",
    "HpeArubaVirtualValidationAdapter",
    "VirtualValidationCoordinator",
    "CapabilityAssessment",
    "SupportDecision",
    "VendorCapabilityContract",
    "VendorCapabilityRegistry",
    "VendorFamily",
]
