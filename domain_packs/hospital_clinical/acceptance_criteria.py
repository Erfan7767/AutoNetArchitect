from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class HospitalAcceptanceCriteria(HospitalDomainBase):
    """Acceptance gates for hospital network technical controls and sensitive paths."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        criteria = [
            {"id": "HOSP-SEG-001", "criterion": "clinical-critical and non-clinical domains are separated with explicit approved flows", "evidence": "segmentation_matrix_and_formal_report", "review": "clinical_security_review"},
            {"id": "HOSP-MED-001", "criterion": "medical and biomedical device paths have current inventory, owner, vendor constraints, and biomedical review", "evidence": "device_inventory_and_review", "review": "biomedical_engineering_review"},
            {"id": "HOSP-WLAN-001", "criterion": "clinical mobility design uses appropriate RF evidence and does not claim validation without survey evidence", "evidence": "rf_confidence_and_survey_report", "review": "clinical_wireless_review"},
            {"id": "HOSP-PACS-001", "criterion": "PACS and imaging flows have measured capacity, prioritization, and loss/latency monitoring", "evidence": "pacs_capacity_and_monitoring", "review": "imaging_service_review"},
            {"id": "HOSP-ACCESS-001", "criterion": "guest, patient, staff, clinical staff, and device access paths are isolated and verified", "evidence": "access_policy_and_formal_report", "review": "security_review"},
            {"id": "HOSP-RES-001", "criterion": "clinical-critical network failure domains and recovery behavior are tested with evidence", "evidence": "resilience_and_dr_test", "review": "clinical_continuity_review"},
            {"id": "HOSP-DEP-001", "criterion": "deployment includes rollback, maintenance window, clinical owner approval, and field feasibility evidence", "evidence": "deployment_gate_and_field_report", "review": "change_and_clinical_review"},
            {"id": "HOSP-CLAIM-001", "criterion": "no clinical safety, medical approval, or regulatory readiness claim is emitted by network design alone", "evidence": "scope_and_claim_audit", "review": "governance_review"},
        ]
        self.record_decision("hospital_acceptance_criteria", [item["id"] for item in criteria], "Clinical-sensitive network paths require evidence plus mandatory human review before production treatment.")
        return self.envelope(
            requirements,
            {
                "criteria": criteria,
                "minimum_status": "all_applicable_criteria_verified",
                "review_threshold": "mandatory_human_review_for_clinically_sensitive_paths",
                "production_claim_requires": ["formal_proof_status", "field_feasibility_pass", "fresh_evidence_chain", "clinical_owner_review", "biomedical_review_when_devices_are_involved"],
                "clinical_readiness_claim": "not_allowed_without_authoritative_human_approval_and_scope",
            },
        )
