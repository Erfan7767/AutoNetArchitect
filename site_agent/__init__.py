"""Secure on-premises foundations for the AutoNetArchitect site agent."""

from .agent import ReadOnlyDiscoveryAgent
from .coordination import AgentAssignment, AgentResponsibility, AgentRole, CoordinationStage, MultiAgentResponsibilityModel
from .discovery_adapters import (
    CiscoDiscoveryAdapter,
    DiscoveryPlan,
    FortinetDiscoveryAdapter,
    HpeArubaDiscoveryAdapter,
    HuaweiDiscoveryAdapter,
    ReadOnlyRequest,
)
from .discovery_coordination import (
    CoordinatedDiscoveryResult,
    DiscoveryBatchResult,
    DiscoveryWorkItem,
    ParallelDiscoveryCoordinator,
)
from .evidence_handoff import DesignEvidenceHandoff, EvidenceBoundHandoffCoordinator
from .models import AgentHealth, DiscoveryResult, DiscoveryTarget, VirtualTestResult
from .scope import AuthorizedScope
from .validation_policy import ScenarioPolicyDecision, ScenarioValidationPolicy, ValidationScenario
from .vendor_support import CapabilityAssessment, SupportDecision, VendorCapabilityContract, VendorCapabilityRegistry, VendorFamily
from .virtual_adapters import (
    CandidateCommitValidationAdapter,
    CiscoVirtualValidationAdapter,
    DigitalTwinValidationAdapter,
    FortinetVirtualValidationAdapter,
    HpeArubaVirtualValidationAdapter,
    HuaweiVirtualValidationAdapter,
    LabValidationAdapter,
    VirtualFidelity,
    VirtualValidationPath,
    VirtualValidationPathAdapter,
    VirtualValidationPlan,
)
from .virtual_validation import VirtualValidationCoordinator

__all__ = [
    "AgentHealth",
    "AuthorizedScope",
    "DiscoveryResult",
    "DiscoveryTarget",
    "ReadOnlyDiscoveryAgent",
    "AgentRole",
    "CoordinationStage",
    "AgentResponsibility",
    "AgentAssignment",
    "MultiAgentResponsibilityModel",
    "DiscoveryWorkItem",
    "CoordinatedDiscoveryResult",
    "DiscoveryBatchResult",
    "ParallelDiscoveryCoordinator",
    "DesignEvidenceHandoff",
    "EvidenceBoundHandoffCoordinator",
    "ReadOnlyRequest",
    "DiscoveryPlan",
    "CiscoDiscoveryAdapter",
    "HuaweiDiscoveryAdapter",
    "FortinetDiscoveryAdapter",
    "HpeArubaDiscoveryAdapter",
    "VirtualTestResult",
    "VirtualFidelity",
    "VirtualValidationPath",
    "VirtualValidationPlan",
    "VirtualValidationPathAdapter",
    "LabValidationAdapter",
    "DigitalTwinValidationAdapter",
    "CandidateCommitValidationAdapter",
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
    "ScenarioPolicyDecision",
    "ValidationScenario",
    "ScenarioValidationPolicy",
]
