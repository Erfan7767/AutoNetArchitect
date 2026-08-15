"""Pydantic v2 contracts for technical compliance assessment."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ComplianceFramework(str, Enum):
    """Supported technical assessment frameworks."""

    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NCA = "nca"
    CIS_BENCHMARK = "cis_benchmark"


class ComplianceState(str, Enum):
    """Conservative state of one control assessment."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class EvidenceDomain(str, Enum):
    """State domain from which technical evidence originates."""

    DESIGN = "design"
    CONFIGURATION = "configuration"
    OPERATIONAL = "operational"
    HUMAN_SUPPLIED = "human_supplied"
    EXTERNAL_AUTHORITY = "external_authority"


class ComplianceScope(BaseModel):
    """Explicit assessment boundary and disclaimer."""

    model_config = ConfigDict(extra="forbid")

    framework: ComplianceFramework
    framework_version: str | None = None
    organization_scope: str | None = None
    system_scope: str | None = None
    sites: list[str] = Field(default_factory=list)
    in_scope_assets: list[str] = Field(default_factory=list)
    excluded_assets: list[str] = Field(default_factory=list)
    assessment_purpose: str = "technical_network_control_assessment"
    technical_only: bool = True
    certification_claim: bool = False
    readiness_claim: bool = False
    disclaimer: str = "This artifact is a technical network control assessment only; it is not a certification, audit opinion, legal opinion, or complete regulatory readiness determination."
    authoritative_obligations_supplied: bool = False
    human_review_required: bool = True

    def model_post_init(self, __context: Any) -> None:
        """Prevent claims outside the declared technical scope."""
        if not self.technical_only:
            raise ValueError("Compliance layer is technical-only")
        if self.certification_claim or self.readiness_claim:
            raise ValueError("certification and full readiness claims are prohibited")
        if not self.disclaimer.strip():
            raise ValueError("scope disclaimer is mandatory")


class EvidenceReference(BaseModel):
    """Traceable evidence reference used by one control."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    domain: EvidenceDomain
    source: str
    control_ids: list[str] = Field(default_factory=list)
    source_record_id: str | None = None
    source_version: str | None = None
    observed_at: datetime | None = None
    freshness_expiry: datetime | None = None
    content_hash: str | None = None
    supports: bool = True
    notes: str | None = None


class ControlDefinition(BaseModel):
    """Framework control mapped to technical network evidence."""

    model_config = ConfigDict(extra="forbid")

    control_id: str
    title: str
    technical_objective: str
    required_evidence_domains: list[EvidenceDomain] = Field(default_factory=list)
    authoritative_reference_required: bool = True
    implementation_examples: list[str] = Field(default_factory=list)
    disclaimer: str = "Technical mapping only; authoritative framework text and organizational interpretation remain required."


class ControlAssessment(BaseModel):
    """Evidence-bounded result for one technical control."""

    model_config = ConfigDict(extra="forbid")

    control: ControlDefinition
    state: ComplianceState
    rationale: str
    evidence: list[EvidenceReference] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_domains_present: list[EvidenceDomain] = Field(default_factory=list)
    human_review_required: bool = True
    production_gate: str = "blocked_pending_authoritative_scope_and_evidence"


class ComplianceAssessment(BaseModel):
    """Complete technical compliance assessment artifact."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: str
    framework: ComplianceFramework
    scope: ComplianceScope
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    controls: list[ControlAssessment] = Field(default_factory=list)
    overall_state: ComplianceState = ComplianceState.NOT_VERIFIABLE
    verified_control_ids: list[str] = Field(default_factory=list)
    partially_verified_control_ids: list[str] = Field(default_factory=list)
    failed_control_ids: list[str] = Field(default_factory=list)
    unverified_control_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evidence_basis: list[str] = Field(default_factory=list)
    sot_basis: dict[str, str] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    certification_statement: str = "No certification, accreditation, audit opinion, or full regulatory readiness claim is made."
    human_review_required: bool = True
    deployment_gate: str = "blocked_pending_review"
    decisions: list[dict[str, Any]] = Field(default_factory=list)


class ComplianceReport(BaseModel):
    """Report wrapper with explicit basis and claims boundary."""

    model_config = ConfigDict(extra="forbid")

    assessment: ComplianceAssessment
    report_language: str = "en"
    report_type: str = "technical_compliance_assessment"
    sot_basis_declared: bool = False
    evidence_basis_declared: bool = False
    disclaimer: str = "Technical network assessment only; review authoritative requirements, organizational scope, non-network controls, and independent audit evidence before making any compliance decision."

    def model_post_init(self, __context: Any) -> None:
        """Require explicit basis declarations in every report."""
        if not self.sot_basis_declared or not self.evidence_basis_declared:
            raise ValueError("Compliance report must declare both SoT basis and evidence basis")
        if self.report_type != "technical_compliance_assessment":
            raise ValueError("unsupported compliance report type")
