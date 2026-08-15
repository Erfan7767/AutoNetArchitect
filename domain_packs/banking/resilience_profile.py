from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingResilienceProfile(BankingDomainBase):
    """Resilience and DR-aware technical patterns for banking networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "local": ["dual_power", "dual_uplink", "redundant_gateway", "failure_domain_separation"],
            "wan": ["diverse_carriers_when_required", "primary_backup_policy", "tested_failover"],
            "dr": ["geographic_diversity", "routing_failover", "replication_path_isolation", "runbook", "evidence_backed_test"],
            "monitoring": ["path_health", "routing_state", "replication_lag", "device_health", "security_events"],
            "production_gate": "no_activation_without_test_evidence_and_approved_runbook",
        }
        self.record_decision("banking_resilience", profile["production_gate"], "Banking resilience requires tested technical failover and approved operational evidence.")
        return self.envelope(requirements, profile)
