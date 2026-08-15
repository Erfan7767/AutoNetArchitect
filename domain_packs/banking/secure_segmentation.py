from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingSecureSegmentation(BankingDomainBase):
    """Strict trust-zone and flow policy baseline for banking networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "zones": ["payment_processing", "atm", "teller", "customer_facing", "staff", "guest", "voice", "iot", "management", "security_tools", "backup_replication"],
            "default_policy": "deny_inter_zone_until_explicitly_approved",
            "flow_controls": ["source_destination_service_identity", "stateful_inspection", "egress_restriction", "admin_path_isolation"],
            "special_controls": ["atm_no_general_user_access", "payment_zone_no_direct_guest_access", "management_only_from_privileged_paths"],
            "evidence_required": ["flow_matrix", "acl_policy", "formal_verification_report", "change_approval"],
        }
        self.record_decision("banking_segmentation", artifact["default_policy"], "Banking trust zones require explicit approved flows and evidence.")
        return self.envelope(requirements, artifact)
