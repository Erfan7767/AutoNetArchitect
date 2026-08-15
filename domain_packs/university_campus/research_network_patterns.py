from __future__ import annotations

from typing import Any

from .common import UniversityDomainBase


class ResearchNetworkPatterns(UniversityDomainBase):
    """Governed research exceptions for throughput, protocols, and external collaboration."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "default_zone": "research_segmented_zone",
            "allowed_exceptions": ["large_data_transfer", "special_protocols", "instrument_networks", "external_research_collaboration"],
            "exception_controls": ["named_owner", "expiry_date", "approved_flow_matrix", "bandwidth_budget", "logging", "formal_verification_or_review"],
            "high_throughput": ["dedicated_uplinks_when_justified", "jumbo_frame_only_with_end_to_end_evidence", "capacity_and_loss_measurement"],
            "internet": "controlled_research_egress_not_general_bypass",
            "review": "research_owner_and_security_review_required",
        }
        self.record_decision("university_research_pattern", artifact["allowed_exceptions"], "Research exceptions are explicit, time-bounded, owned, and reviewable.")
        return self.envelope(requirements, artifact)
