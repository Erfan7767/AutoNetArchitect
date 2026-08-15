from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class UniversityAcceptanceCriteria(UniversityDomainBase):
    """Domain-specific acceptance gates for heterogeneous campus networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        criteria = [
            {"id": "UNI-FUNC-001", "criterion": "academic, administrative, research, residential, and guest domains are modeled separately", "evidence": "requirements_and_segmentation_profile", "review": "architecture_review"},
            {"id": "UNI-WLAN-001", "criterion": "high-density wireless planning uses area, client, application, and interference inputs", "evidence": "rf_confidence_and_survey_report", "review": "wireless_review"},
            {"id": "UNI-ID-001", "criterion": "student, faculty, staff, researcher, guest, and device access policies have ownership and lifecycle", "evidence": "identity_access_and_operations_records", "review": "identity_security_review"},
            {"id": "UNI-RES-001", "criterion": "research exceptions are named, time-bounded, bandwidth-accountable, and logged", "evidence": "research_exception_register", "review": "research_owner_and_security_review"},
            {"id": "UNI-MCAST-001", "criterion": "multicast and video scope, receiver scale, platform support, and loss monitoring are documented", "evidence": "multicast_video_design_and_validation", "review": "media_service_review"},
            {"id": "UNI-DORM-001", "criterion": "residential access isolates residents and models peak demand separately from academic access", "evidence": "dormitory_capacity_and_segmentation", "review": "residential_network_review"},
            {"id": "UNI-OPS-001", "criterion": "wireless, identity, services, incidents, changes, and ownership integrate with operations", "evidence": "operations_integration_evidence", "review": "operations_review"},
            {"id": "UNI-PROOF-001", "criterion": "production claims declare formal proof, field feasibility, and evidence freshness", "evidence": "verification_field_and_knowledge_reports", "review": "governance_review"},
        ]
        self.record_decision("university_acceptance_criteria", [item["id"] for item in criteria], "Campus acceptance requires evidence across heterogeneous functions, identity, wireless, services, and operations.")
        return self.envelope(requirements, {
            "criteria": criteria,
            "minimum_status": "all_applicable_criteria_verified",
            "review_threshold": "enhanced_domain_review",
            "production_claim_requires": ["formal_proof_status", "field_feasibility_pass", "fresh_evidence_chain", "functional_owner_approval", "operations_integration"],
            "academic_or_research_readiness_claim": "not_allowed_without_authoritative_scope_and_owner_evidence",
        })
