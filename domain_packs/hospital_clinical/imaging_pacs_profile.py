from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class ImagingPACSProfile(HospitalDomainBase):
    """PACS and imaging network profile with bandwidth and latency sensitivity."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        artifact = {
            "traffic_classes": ["modalities_to_pacs", "pacs_to_viewers", "replication_and_archive", "clinical_viewing", "administrative_access"],
            "sensitivity": {"bandwidth": "high", "latency": "workflow_dependent", "loss": "must_be_measured_and_reviewed", "burst": "possible_during_modality_and_archive_windows"},
            "planning_inputs": ["study_size", "studies_per_hour", "concurrent_viewers", "replication_targets", "retention_and_archive_flow"],
            "controls": ["dedicated_or_prioritized_paths", "pacs_zone_isolation", "capacity_headroom", "monitoring_for_loss_latency_and_utilization"],
            "clinical_review": self.clinical_review(requirements, "pacs_imaging"),
        }
        self.record_decision("hospital_pacs_profile", artifact["sensitivity"], "PACS design uses measured workload and clinical review rather than invented imaging volumes.")
        return self.envelope(requirements, artifact)
