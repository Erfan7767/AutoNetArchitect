from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingNetworksPack(BankingDomainBase):
    """Entry point for the opt-in Banking Networks domain pack."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        self.record_decision(
            "banking_domain_activation",
            "banking",
            "Activate banking-specific network and technical-control patterns only after explicit sector selection.",
            alternatives=["enterprise_corporate_pack", "healthcare_pack", "public_sector_pack"],
            rejection_reasons={"compliance": "This activation is not a regulatory certification."},
        )
        return self.envelope(
            requirements,
            {
                "status": "active",
                "in_scope": [
                    "branch_banking_topology",
                    "core_network_segmentation",
                    "atm_and_remote_banking_connectivity",
                    "privileged_access_separation",
                    "audit_logging_controls",
                    "resilience_and_dr_technical_patterns",
                ],
                "out_of_scope": [
                    "regulatory_certification",
                    "legal_interpretation",
                    "business_continuity_program_management",
                    "application_security_architecture",
                    "payment_scheme_certification",
                ],
                "review_threshold": "enhanced_manual_review",
            },
        )
