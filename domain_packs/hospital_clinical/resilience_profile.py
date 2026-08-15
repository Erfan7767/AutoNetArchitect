from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class HospitalResilienceProfile(HospitalDomainBase):
    """Higher availability and recovery expectations for clinical networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "clinical_critical": ["dual_power", "dual_uplink", "redundant_gateway", "tested_failover", "local_survivability_when_required", "continuous_monitoring"],
            "non_clinical": ["risk_based_redundancy", "documented_backup_path", "scheduled_recovery_test"],
            "dr": ["geographic_diversity", "clinical_service_priority", "routing_and_dns_failover", "approved_runbook", "evidence_backed_test"],
            "production_gate": "no_clinical_activation_without_human_review_and_test_evidence",
        }
        self.record_decision("hospital_resilience", artifact["production_gate"], "Clinical critical paths receive higher availability and review thresholds.")
        return self.envelope(requirements, artifact)
