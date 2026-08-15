from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingRequirementsProfile(BankingDomainBase):
    """High-assurance requirement profile for banking network programs."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "mandatory_inputs": [
                "legal_entity_and_jurisdictions",
                "branch_and_atm_inventory",
                "critical_services_and_payment_flows",
                "trust_zone_inventory",
                "privileged_roles_and_admin_paths",
                "retention_and_audit_obligations",
                "rpo_rto_targets",
                "third_party_connectivity",
            ],
            "high_assurance_inputs": [
                "formal_verification_scope",
                "change_approval_authority",
                "break_glass_procedure",
                "dual_control_requirements",
                "dr_test_evidence",
                "equipment_lifecycle_evidence",
            ],
            "default_objectives": [
                "segregate_payment_and_customer_trust_zones",
                "minimize_privileged_access_paths",
                "retain tamper_evident_audit_evidence".replace(" ", "_"),
                "remove_single_points_of_failure",
                "make_deployment_reversible_and_approved",
            ],
            "unresolved_input_policy": "block_or_manual_review_not_silent_defaulting",
        }
        self.record_decision(
            "banking_requirements_profile",
            profile["default_objectives"],
            "Banking network requirements prioritize control evidence, segmentation, auditability, and resilience.",
        )
        return self.envelope(requirements, profile)
