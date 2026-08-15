from __future__ import annotations

from typing import Any

from .common import HospitalDomainBase


class MedicalDeviceConstraints(HospitalDomainBase):
    """Conservative network constraints for medical and biomedical devices."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        device_inventory = requirements.get("medical_device_inventory")
        review = self.clinical_review(requirements, "medical_device_constraints")
        artifact = {
            "status": "blocked_missing_device_inventory" if device_inventory is None else "review_required",
            "device_inventory_source": "human_supplied_or_authoritative_asset_registry",
            "constraints": [
                "do_not_change_vlan_or_qos_without_biomedical_and_vendor_review",
                "preserve_vendor_documented_protocols_and_ports",
                "avoid_active_scanning_without_approved_safety_window",
                "isolate_legacy_devices_with_compensating_controls",
                "maintain_time_and_name_resolution_dependencies",
                "record_device_owner_and_support_window",
            ],
            "unknown_behavior": "do_not_infer_device_compatibility_or_clinical_impact",
            "clinical_review": review,
        }
        self.record_decision("medical_device_constraints", artifact["status"], "Medical device network changes require biomedical, clinical, and vendor evidence.")
        return self.envelope(requirements, artifact)
