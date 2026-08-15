from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingBranchPatterns(BankingDomainBase):
    """Branch network patterns for teller, staff, ATM, and local services."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        patterns = {
            "standard_branch": {
                "zones": ["staff", "teller", "atm", "guest", "management", "voice"],
                "edge": "managed_dual_wan_when_critical",
                "local_breakout": "restricted_and_logged",
                "failover": "documented_primary_backup_path",
            },
            "small_branch": {
                "zones": ["staff", "atm", "management"],
                "edge": "single_edge_with_approved_backup",
                "local_breakout": "restricted",
                "failover": "manual_or_semi_automatic_reviewed",
            },
            "cash_intensive_branch": {
                "zones": ["staff", "teller", "atm", "security_systems", "management"],
                "edge": "dual_edge_and_diverse_carriers",
                "local_breakout": "explicitly approved",
                "failover": "tested_and_monitored",
            },
        }
        selected = requirements.get("branch_pattern", "standard_branch")
        if selected not in patterns:
            self.record_assumption("branch_pattern", selected, "Branch pattern requires validation against physical and service inventory.")
            selected = "standard_branch"
        self.record_decision("banking_branch_pattern", selected, "Branch pattern is selected from explicit banking branch characteristics.")
        return self.envelope(requirements, {"selected": selected, "patterns": patterns})
