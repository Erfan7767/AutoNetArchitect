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
from .enrollment import EnrollmentReceipt, MutualEnrollmentAuthority, PinnedMutualEnrollmentAuthority
from .evidence_handoff import DesignEvidenceHandoff, EvidenceBoundHandoffCoordinator
from .exact_capability import ExactCapabilityAssessor, ExactCapabilityEvidence
from .models import AgentHealth, DiscoveryResult, DiscoveryTarget, VirtualTestResult
from .runtime import EnrolledReadOnlyAgent
from .scope import AuthorizedScope
from .trust import Ed25519PinnedSignatureVerifier, PinnedTrustStore
from .team_graph import MultiAgentTeamGraph, TeamGraphEvaluation
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
    "EnrolledReadOnlyAgent",
    "EnrollmentReceipt",
    "MutualEnrollmentAuthority",
    "PinnedMutualEnrollmentAuthority",
    "PinnedTrustStore",
    "Ed25519PinnedSignatureVerifier",
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
    "MultiAgentTeamGraph",
    "TeamGraphEvaluation",
    "ExactCapabilityEvidence",
    "ExactCapabilityAssessor",
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
