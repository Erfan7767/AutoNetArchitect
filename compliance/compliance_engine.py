"""Evidence-gated technical compliance assessment engine."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Mapping, Sequence

from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord
from source_of_truth.sot_manager import SoTManager, SoTType, SoTError

from ._common import assumption, decision, decision_dict, state_from_evidence, unique
from .compliance_models import ComplianceAssessment, ComplianceFramework, ComplianceReport, ComplianceScope, ComplianceState, ControlAssessment, ControlDefinition, EvidenceDomain, EvidenceReference
from .scope_definitions import controls_for, default_scope


class ComplianceEngine:
    """Run technical-only compliance assessments without making certification claims."""

    def __init__(self, *, audit_trail: AuditTrail | None = None, sot_manager: SoTManager | None = None) -> None:
        """Initialize optional audit and SoT integrations."""
        self.audit_trail = audit_trail
        self.sot_manager = sot_manager
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def assess(self, *, framework: ComplianceFramework | str, scope: ComplianceScope | None = None, evidence: Sequence[EvidenceReference] = (), control_observations: Mapping[str, Mapping[str, Any]] | None = None, sot_basis: Mapping[str, str] | None = None, actor: str = "compliance-engine") -> ComplianceAssessment:
        """Assess controls from explicitly mapped evidence and observations."""
        selected_framework = ComplianceFramework(framework)
        selected_scope = scope or default_scope(selected_framework)
        basis = dict(sot_basis or {})
        basis.update(self._resolve_sot_basis())
        if not basis:
            basis = {"status": "unavailable", "reason": "no SoT manager or explicit SoT basis supplied"}
            self.assumptions.append(assumption("compliance:sot_basis", "unavailable", "reports must state when authoritative SoT basis is unavailable", True))
        references = {item.evidence_id: item for item in evidence}
        controls: list[ControlAssessment] = []
        observations = control_observations or {}
        for control in controls_for(selected_framework):
            observation = dict(observations.get(control.control_id, {}))
            evidence_ids = [str(item) for item in observation.get("evidence_ids", [])]
            mapped = [item for item in evidence if item.evidence_id in evidence_ids or control.control_id in item.control_ids]
            supporting = sum(1 for item in mapped if item.supports)
            contradicting = sum(1 for item in mapped if not item.supports)
            present_domains = {item.domain.value for item in mapped if item.supports}
            required_domains = {item.value for item in control.required_evidence_domains}
            explicit_status = str(observation.get("status", "")).lower()
            if explicit_status == ComplianceState.FAILED.value:
                state = ComplianceState.FAILED.value
                rationale = "explicit control observation marked the control failed"
                missing = sorted(required_domains - present_domains)
            else:
                state, rationale, missing = state_from_evidence(selected_scope.authoritative_obligations_supplied, supporting, contradicting, required_domains, present_domains)
            if explicit_status == ComplianceState.NOT_APPLICABLE.value:
                state = ComplianceState.NOT_APPLICABLE.value
                rationale = "control was explicitly marked not applicable by the supplied assessment context"
            control_assessment = ControlAssessment(control=control, state=state, rationale=rationale, evidence=mapped, missing_evidence=missing, assumptions=list(observation.get("assumptions", [])), sot_basis=basis, evidence_domains_present=[EvidenceDomain(value) for value in sorted(present_domains) if value in {item.value for item in EvidenceDomain}], human_review_required=True, production_gate="allowed_for_technical_review_only" if state == ComplianceState.VERIFIED.value else "blocked_pending_review_and_missing_evidence")
            controls.append(control_assessment)
        assessment = self._aggregate(selected_framework, selected_scope, controls, basis, evidence)
        self.decisions.append(decision("ComplianceEngine", assessment.assessment_id, "technical_evidence_mapping", "map controls only to explicit evidence and state the SoT basis", ["technical_evidence_mapping", "claim_certification_readiness"], {"technical_evidence_mapping": "selected", "claim_certification_readiness": "prohibited"}))
        assessment.decisions = [decision_dict(item) for item in self.decisions]
        if self.audit_trail is not None:
            self.audit_trail.record("compliance.assessment", actor, {"assessment_id": assessment.assessment_id, "framework": selected_framework.value, "overall_state": assessment.overall_state.value, "control_count": len(controls), "evidence_basis": assessment.evidence_basis, "sot_basis": assessment.sot_basis, "certification_claim": False}, outcome="success", correlation_id=assessment.assessment_id)
        return assessment

    def report(self, assessment: ComplianceAssessment, *, language: str = "en") -> ComplianceReport:
        """Create a report that explicitly declares SoT and evidence basis."""
        if language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        return ComplianceReport(assessment=assessment, report_language=language, sot_basis_declared=bool(assessment.sot_basis), evidence_basis_declared=bool(assessment.evidence_basis))

    def assess_hipaa(self, **kwargs: Any) -> ComplianceAssessment:
        """Assess HIPAA technical network mappings."""
        return self.assess(framework=ComplianceFramework.HIPAA, **kwargs)

    def assess_pci(self, **kwargs: Any) -> ComplianceAssessment:
        """Assess PCI DSS technical network mappings."""
        return self.assess(framework=ComplianceFramework.PCI_DSS, **kwargs)

    def assess_iso27001(self, **kwargs: Any) -> ComplianceAssessment:
        """Assess ISO/IEC 27001 technical network mappings."""
        return self.assess(framework=ComplianceFramework.ISO_27001, **kwargs)

    def assess_nca(self, **kwargs: Any) -> ComplianceAssessment:
        """Assess NCA technical mappings pending authoritative edition and scope."""
        return self.assess(framework=ComplianceFramework.NCA, **kwargs)

    def assess_cis_benchmark(self, **kwargs: Any) -> ComplianceAssessment:
        """Assess CIS-style device hardening mappings pending exact benchmark version."""
        return self.assess(framework=ComplianceFramework.CIS_BENCHMARK, **kwargs)

    def _aggregate(self, framework: ComplianceFramework, scope: ComplianceScope, controls: list[ControlAssessment], basis: Mapping[str, str], evidence: Sequence[EvidenceReference]) -> ComplianceAssessment:
        """Aggregate control states conservatively."""
        verified = [item.control.control_id for item in controls if item.state == ComplianceState.VERIFIED]
        partial = [item.control.control_id for item in controls if item.state == ComplianceState.PARTIALLY_VERIFIED]
        failed = [item.control.control_id for item in controls if item.state == ComplianceState.FAILED]
        unverified = [item.control.control_id for item in controls if item.state == ComplianceState.NOT_VERIFIABLE]
        if failed:
            overall = ComplianceState.FAILED
        elif controls and len(verified) == len(controls) and scope.authoritative_obligations_supplied and basis.get("status") != "unavailable":
            overall = ComplianceState.VERIFIED
        elif verified or partial:
            overall = ComplianceState.PARTIALLY_VERIFIED
        else:
            overall = ComplianceState.NOT_VERIFIABLE
        evidence_basis = unique([item.evidence_id for control in controls for item in control.evidence]) or ["none: no control evidence was mapped"]
        assumptions = unique([item for control in controls for item in control.assumptions] + [item.key for item in self.assumptions])
        limitations = ["Technical network controls only; non-network, organizational, legal, privacy, physical, workforce, and audit procedures are outside this artifact.", "Framework control names and mappings are bounded planning mappings until the authoritative edition, applicability, and organizational interpretation are supplied.", "No certification, accreditation, audit opinion, or full readiness claim is made."]
        return ComplianceAssessment(assessment_id=f"compliance:{framework.value}:{uuid.uuid4()}", framework=framework, scope=scope, controls=controls, overall_state=overall, verified_control_ids=verified, partially_verified_control_ids=partial, failed_control_ids=failed, unverified_control_ids=unverified, assumptions=assumptions, evidence_basis=evidence_basis, sot_basis=dict(basis), limitations=limitations, deployment_gate="blocked_pending_review" if overall != ComplianceState.VERIFIED else "technical_review_only")

    def _resolve_sot_basis(self) -> dict[str, str]:
        """Resolve available SoT records without blocking report creation."""
        if self.sot_manager is None:
            return {}
        resolved: dict[str, str] = {}
        for sot_type in SoTType:
            try:
                resolved[sot_type.value] = self.sot_manager.authoritative(sot_type).record_id
            except SoTError:
                resolved[f"{sot_type.value}_status"] = "missing_or_conflicting"
        return resolved
