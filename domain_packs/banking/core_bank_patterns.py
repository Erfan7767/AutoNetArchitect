from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingCorePatterns(BankingDomainBase):
    """Core and data-center-adjacent patterns for banking trust zones."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        pattern = {
            "architecture": "redundant_core_with_separate_security_and_service_transit",
            "zones": ["payment_processing", "customer_data", "channel_services", "management", "security_tools", "backup_replication"],
            "routing_boundary": "controlled_between_security_zones",
            "east_west": "inspection_or_explicit_policy_for_sensitive_zones",
            "failure_domains": ["device", "rack", "power", "site", "provider"],
            "change_gate": "dual_approval_and_pre_change_verification",
        }
        self.record_decision("banking_core_pattern", pattern["architecture"], "Sensitive banking workloads require separated trust zones and independent failure domains.")
        return self.envelope(requirements, pattern)
