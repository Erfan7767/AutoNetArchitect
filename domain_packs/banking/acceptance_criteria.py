from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingAcceptanceCriteria(BankingDomainBase):
    """High-threshold acceptance criteria for banking network technical controls."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        criteria = [
            {"id": "BANK-SEG-001", "criterion": "payment, ATM, customer-facing, staff, guest, voice, IoT, and management zones have explicit boundaries", "evidence": "segmentation_matrix_and_formal_report", "review": "independent_security_review"},
            {"id": "BANK-ADM-001", "criterion": "privileged access is separated, MFA-protected, approved, session-recorded, and time-bound", "evidence": "privileged_access_evidence", "review": "security_and_governance_review"},
            {"id": "BANK-AUD-001", "criterion": "administrative, policy, routing, VPN, and failover events are centralized and tamper-evident", "evidence": "audit_logging_evidence", "review": "audit_control_review"},
            {"id": "BANK-ATM-001", "criterion": "ATM and remote banking paths use approved connectivity classes and continuous monitoring", "evidence": "atm_connectivity_and_monitoring", "review": "service_owner_and_security_review"},
            {"id": "BANK-RES-001", "criterion": "critical failure domains, DR paths, and failover behavior are tested with evidence", "evidence": "dr_test_and_verification_report", "review": "resilience_review"},
            {"id": "BANK-EQP-001", "criterion": "equipment recommendations have current capability, lifecycle, security, and lab evidence", "evidence": "knowledge_and_bom_evidence", "review": "architecture_board_review"},
            {"id": "BANK-CHG-001", "criterion": "deployment has formal proof status, approved rollback, and independent change approval", "evidence": "verification_and_deployment_gate", "review": "change_authority_review"},
            {"id": "BANK-CMP-001", "criterion": "each regulatory claim has authoritative evidence, jurisdiction, freshness, and control mapping", "evidence": "knowledge_authority_and_compliance_mapping", "review": "compliance_officer_review"},
        ]
        self.record_decision("banking_acceptance_criteria", [item["id"] for item in criteria], "Banking production acceptance requires technical evidence and enhanced independent review.")
        return self.envelope(
            requirements,
            {
                "criteria": criteria,
                "minimum_status": "all_applicable_criteria_verified",
                "review_threshold": "enhanced_manual_review",
                "production_claim_requires": [
                    "explicit_proof_status_verified",
                    "fresh_evidence_chain",
                    "field_feasibility_pass",
                    "approved_change_record",
                    "independent_security_review",
                    "independent_compliance_review",
                ],
                "compliance_readiness_claim": "not_allowed_without_authoritative_evidence_and_scope",
            },
        )
