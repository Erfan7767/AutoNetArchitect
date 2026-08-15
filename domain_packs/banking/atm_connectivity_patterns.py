from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingATMConnectivityPatterns(BankingDomainBase):
    """ATM and remote banking connectivity classes with explicit service isolation."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        classes = {
            "atm_managed_private": {"transport": "private_or_managed_vpn", "segmentation": "dedicated_atm_zone", "internet": "denied_by_default", "monitoring": "continuous"},
            "atm_remote_site": {"transport": "dual_path_when_critical", "segmentation": "dedicated_atm_zone", "internet": "no_direct_internet", "monitoring": "continuous"},
            "remote_banking_channel": {"transport": "controlled_secure_edge", "segmentation": "channel_services_zone", "internet": "edge_firewall_and_ddos_controls", "monitoring": "transaction_path_audit"},
        }
        selected = requirements.get("connectivity_class", "atm_managed_private")
        if selected not in classes:
            self.record_assumption("connectivity_class", selected, "ATM connectivity class requires validation from service and carrier contracts.")
            selected = "atm_managed_private"
        self.record_decision("banking_atm_connectivity", selected, "ATM and remote banking paths are isolated and continuously monitored.")
        return self.envelope(requirements, {"selected": selected, "classes": classes, "mandatory_review": True})
