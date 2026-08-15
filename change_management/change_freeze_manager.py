"""Change freeze calendar enforcement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Sequence

from .change_models import ChangeRequest, ChangeType, ChangeStatus, FreezeType


@dataclass(frozen=True)
class FreezeWindow:
    """One explicit freeze interval."""

    freeze_id: str
    start_time: datetime
    end_time: datetime
    freeze_type: str
    reason: str
    sector: str = "general"
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize freeze window."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class FreezeEvaluation:
    """Decision for scheduling inside a freeze window."""

    allowed: bool
    freeze_ids: tuple[str, ...]
    required_approvals: tuple[str, ...]
    reasons: tuple[str, ...]
    override_record_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize freeze evaluation."""
        return asdict(self) | {"freeze_ids": list(self.freeze_ids), "required_approvals": list(self.required_approvals), "reasons": list(self.reasons)}


class ChangeFreezeManager:
    """Maintain local freeze windows and enforce policy before scheduling."""

    def __init__(self) -> None:
        """Create an empty freeze calendar."""
        self._windows: list[FreezeWindow] = []

    def add_window(self, window: FreezeWindow) -> FreezeWindow:
        """Add a validated freeze interval."""
        if window.end_time <= window.start_time:
            raise ValueError("freeze end must be later than freeze start")
        if window.freeze_type not in {item.value for item in FreezeType}:
            raise ValueError("unsupported freeze type")
        self._windows.append(window)
        return window

    def windows(self) -> tuple[FreezeWindow, ...]:
        """Return freeze windows in calendar order."""
        return tuple(sorted(self._windows, key=lambda item: (item.start_time, item.freeze_id)))

    def evaluate(self, request: ChangeRequest, start_time: datetime, end_time: datetime, *, emergency_override: bool = False, enhanced_approval: bool = False) -> FreezeEvaluation:
        """Evaluate a requested interval against active freezes."""
        active = tuple(window for window in self._windows if start_time < window.end_time and end_time > window.start_time)
        if not active:
            return FreezeEvaluation(True, (), (), ("no active freeze intersects the requested interval",))
        ids = tuple(window.freeze_id for window in active)
        requirements: list[str] = []
        reasons: list[str] = []
        for window in active:
            if window.freeze_type == FreezeType.FULL_FREEZE.value:
                if request.change_type == ChangeType.EMERGENCY.value and emergency_override and enhanced_approval:
                    requirements.append("emergency_freeze_override")
                    reasons.append(f"full freeze {window.freeze_id} overridden by emergency change with enhanced approval")
                else:
                    reasons.append(f"full freeze {window.freeze_id} blocks scheduling")
                    return FreezeEvaluation(False, ids, ("enhanced_emergency_approval",), tuple(reasons), True)
            elif window.freeze_type == FreezeType.PARTIAL_FREEZE.value and request.change_type != ChangeType.STANDARD.value:
                reasons.append(f"partial freeze {window.freeze_id} permits standard changes only")
                return FreezeEvaluation(False, ids, ("freeze_exception_approval",), tuple(reasons), False)
            elif window.freeze_type == FreezeType.SOFT_FREEZE.value:
                if not enhanced_approval:
                    reasons.append(f"soft freeze {window.freeze_id} requires additional approval")
                    return FreezeEvaluation(False, ids, ("soft_freeze_additional_approval",), tuple(reasons), False)
                requirements.append("soft_freeze_additional_approval")
        return FreezeEvaluation(True, ids, tuple(dict.fromkeys(requirements)), tuple(reasons), bool(requirements))
