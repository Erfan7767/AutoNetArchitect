"""Conflict detection between overlapping network change requests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .change_models import ChangeRequest


@dataclass(frozen=True)
class ChangeConflict:
    """One detected change conflict."""

    conflict_id: str
    conflict_type: str
    change_ids: tuple[str, ...]
    detail: str
    recommended_resolution: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize conflict."""
        return asdict(self) | {"change_ids": list(self.change_ids)}


@dataclass(frozen=True)
class ConflictReport:
    """Aggregate conflict report."""

    conflicts: tuple[ChangeConflict, ...]
    blocking: bool
    rationale: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize conflict report."""
        return {"conflicts": [item.to_dict() for item in self.conflicts], "blocking": self.blocking, "rationale": list(self.rationale)}


class ChangeConflictDetector:
    """Detect conflicts using explicit scopes, windows, and config sections."""

    def detect(self, requests: Sequence[ChangeRequest], *, dependencies: Mapping[str, Sequence[str]] | None = None) -> ConflictReport:
        """Return conflicts for overlapping scheduled windows."""
        conflicts: list[ChangeConflict] = []
        dependencies = dependencies or {}
        for index, left in enumerate(requests):
            for right in requests[index + 1:]:
                if not self._overlap(left, right):
                    continue
                left_devices = {device.device_id for device in left.affected_devices}
                right_devices = {device.device_id for device in right.affected_devices}
                overlap_devices = sorted(left_devices & right_devices)
                if overlap_devices:
                    conflicts.append(ChangeConflict(f"conflict:{left.change_id}:{right.change_id}:device", "device_conflict", (left.change_id, right.change_id), f"same devices in overlapping windows: {', '.join(overlap_devices)}", "reschedule one change or merge after technical review"))
                left_services = {service.service_id for service in left.affected_services}
                right_services = {service.service_id for service in right.affected_services}
                overlap_services = sorted(left_services & right_services)
                if overlap_services:
                    conflicts.append(ChangeConflict(f"conflict:{left.change_id}:{right.change_id}:service", "service_conflict", (left.change_id, right.change_id), f"same services in overlapping windows: {', '.join(overlap_services)}", "reschedule or obtain service-owner decision"))
                if left.requester and left.requester == right.requester:
                    conflicts.append(ChangeConflict(f"conflict:{left.change_id}:{right.change_id}:resource", "resource_conflict", (left.change_id, right.change_id), "same requester is assigned to overlapping changes", "assign separate resource or reschedule"))
                if right.change_id in dependencies.get(left.change_id, ()) or left.change_id in dependencies.get(right.change_id, ()):
                    conflicts.append(ChangeConflict(f"conflict:{left.change_id}:{right.change_id}:dependency", "dependency_conflict", (left.change_id, right.change_id), "declared change dependency intersects an overlapping window", "schedule dependency before dependent change"))
                conflicts.extend(self._logical_conflicts(left, right))
        return ConflictReport(tuple(conflicts), bool(conflicts), ("overlapping windows are required before conflicts are considered blocking",))

    @staticmethod
    def _overlap(left: ChangeRequest, right: ChangeRequest) -> bool:
        """Return whether two scheduled intervals overlap."""
        if left.scheduled_window is None or right.scheduled_window is None:
            return False
        return left.scheduled_window.start_time < right.scheduled_window.end_time and right.scheduled_window.start_time < left.scheduled_window.end_time

    @staticmethod
    def _logical_conflicts(left: ChangeRequest, right: ChangeRequest) -> list[ChangeConflict]:
        """Detect contradictory after-config values for the same section."""
        conflicts: list[ChangeConflict] = []
        left_map = {(item.device_id, item.change_section): item.after_config for item in left.config_changes}
        right_map = {(item.device_id, item.change_section): item.after_config for item in right.config_changes}
        for key in sorted(set(left_map) & set(right_map)):
            if left_map[key] and right_map[key] and left_map[key] != right_map[key]:
                conflicts.append(ChangeConflict(f"conflict:{left.change_id}:{right.change_id}:logical:{key[0]}:{key[1]}", "logical_conflict", (left.change_id, right.change_id), f"contradictory after-config values for {key[0]} {key[1]}", "merge the intended state or prioritize one change"))
        return conflicts
