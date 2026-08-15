from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingAuditLoggingProfile(BankingDomainBase):
    """Enhanced audit and logging profile for network technical controls."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        profile = {
            "events": ["authentication", "authorization", "configuration_change", "policy_change", "routing_change", "vpn_event", "failover_event", "admin_session", "time_sync", "device_health"],
            "collection": "centralized_and_tamper_evident",
            "transport": "authenticated_encrypted_transport",
            "time": "trusted_time_source_required",
            "retention": "organization_and_regulator_supplied",
            "correlation": ["identity", "device", "change_ticket", "approval", "source_ip", "result"],
            "review": "continuous_alerting_plus_periodic_control_review",
            "evidence_required": ["collector_health", "retention_config", "sample_event_chain", "access_review"],
        }
        if not requirements.get("retention_policy"):
            self.record_assumption("retention_policy", None, "Exact retention is organization- and jurisdiction-specific and must be supplied.")
        self.record_decision("banking_audit_logging", profile["collection"], "Network audit events must be centralized, authenticated, time-correlated, and reviewable.")
        return self.envelope(requirements, profile)
