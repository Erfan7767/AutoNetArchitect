"""Safety gates for production firmware workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .firmware_manager import BootMode, FirmwareSafetyAssessment, FirmwareUpgradeRequest, ImageIntegrityResult, UpgradePath


class FirmwareSafetyChecks:
    """Evaluate firmware requests before any upgrade driver can be called."""

    SUPPORTED_PATH_STATES = frozenset({"supported", "supported_with_evidence", "supported_with_license"})
    REQUIRED_APPROVAL_REFERENCE_PREFIX = "approval://"

    def assess(self, request: FirmwareUpgradeRequest, path: UpgradePath | None, integrity: ImageIntegrityResult, in_flight_groups: Iterable[str] = ()) -> FirmwareSafetyAssessment:
        """Return a conservative gate for the supplied request."""
        reasons: list[str] = []
        required_inputs: list[str] = []
        prechecks: list[str] = []
        evidence = set(request.evidence_ids)
        evidence.update(request.image.evidence_ids)
        if path is not None:
            evidence.update(path.evidence_ids)
        execution_requested = not request.dry_run
        if not request.project_valid:
            reasons.append("project state is invalid or unresolved")
        if request.unresolved_human_inputs:
            reasons.extend(str(item) for item in request.unresolved_human_inputs)
        if path is None:
            reasons.append("no exact registered upgrade path for vendor/platform/model/current-version/target-version/boot-mode")
            required_inputs.append("exact_upgrade_path_evidence")
        else:
            if path.support_state not in self.SUPPORTED_PATH_STATES:
                reasons.append("registered upgrade path is not explicitly supported")
            if not path.evidence_ids:
                reasons.append("upgrade path has no traceable evidence IDs")
                required_inputs.append("upgrade_path_evidence_ids")
        if execution_requested and not integrity.verified:
            reasons.append(f"firmware image integrity is not verified: {integrity.status}")
            required_inputs.append("verified_firmware_image_sha256")
        if request.target.current_boot_mode == BootMode.UNKNOWN.value or request.image.boot_mode == BootMode.UNKNOWN.value:
            reasons.append("boot mode is unknown for a path where boot-mode awareness is required")
            required_inputs.append("confirmed_boot_mode")
        if request.image.boot_mode == BootMode.BOOTLOADER.value or (path is not None and path.target_boot_mode == BootMode.BOOTLOADER.value):
            reasons.append("bootloader image execution is outside the limited V1 workflow")
            required_inputs.append("supported_non_bootloader_upgrade_path")
        active_groups = set(str(item) for item in in_flight_groups)
        group = request.target.redundancy_group
        if group and group in active_groups:
            reasons.append("another member of the same redundancy group is already in flight")
            prechecks.append("complete_current_redundancy_group_operation")
        if execution_requested:
            if request.maintenance_window is None:
                reasons.append("firmware execution requires an approved maintenance window")
                required_inputs.append("maintenance_window")
            else:
                window = request.maintenance_window
                if window.end_time <= window.start_time:
                    reasons.append("maintenance window end must be later than start")
                if window.start_time.tzinfo is None or window.end_time.tzinfo is None:
                    reasons.append("maintenance window timestamps must include timezone information")
                if not window.business_justification.strip():
                    reasons.append("maintenance window requires a business justification")
                    required_inputs.append("maintenance_window_business_justification")
                if not window.affected_users_notified:
                    reasons.append("affected users must be notified before firmware execution")
                    required_inputs.append("affected_users_notified")
            if not request.approved:
                reasons.append("firmware execution requires explicit approval")
                required_inputs.append("approved")
            if not request.approval_reference:
                reasons.append("approval reference is missing")
                required_inputs.append("approval_reference")
            elif not request.approval_reference.startswith(self.REQUIRED_APPROVAL_REFERENCE_PREFIX):
                reasons.append("approval reference must be a traceable approval:// reference")
                required_inputs.append("approval_reference")
            if not request.actor:
                reasons.append("firmware execution requires an identified actor")
                required_inputs.append("actor")
            rollback_id = request.rollback_image_id or (path.rollback_image_id if path else "")
            if request.rollback_required and not rollback_id:
                reasons.append("rollback image reference is mandatory for firmware execution")
                required_inputs.append("rollback_image_id")
            prechecks.extend(("confirm target identity", "confirm maintenance window", "confirm image digest", "confirm rollback image", "verify post-upgrade health"))
        allowed = not reasons
        safety_class = "firmware_upgrade_disruptive" if execution_requested else "firmware_upgrade_preview"
        return FirmwareSafetyAssessment(allowed, safety_class, tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(required_inputs)), tuple(dict.fromkeys(prechecks)), tuple(sorted(evidence)))

    @staticmethod
    def redundancy_group_available(group: str, in_flight_groups: Iterable[str]) -> bool:
        """Return whether a redundancy group has no currently executing member."""
        return not group or group not in {str(item) for item in in_flight_groups}
