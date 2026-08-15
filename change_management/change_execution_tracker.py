"""Execution tracking for change implementation steps."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from log_redaction.redacting_filter import RedactingFilter

from .change_models import ChangeRequest, ChangeStatus, ExecutionEvent, ExecutionStatus, StepStatus


@dataclass(frozen=True)
class ExecutionSummary:
    """Current execution state."""

    overall_status: str
    current_step: int
    completed_steps: int
    total_steps: int
    started_at: datetime | None
    elapsed_seconds: float
    estimated_remaining_seconds: float | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize execution summary."""
        return {"overall_status": self.overall_status, "current_step": self.current_step, "completed_steps": self.completed_steps, "total_steps": self.total_steps, "started_at": self.started_at.isoformat() if self.started_at else None, "elapsed_seconds": self.elapsed_seconds, "estimated_remaining_seconds": self.estimated_remaining_seconds}


class ChangeExecutionTracker:
    """Track execution events without becoming a remote executor."""

    def start(self, request: ChangeRequest, *, actor: str) -> ExecutionSummary:
        """Start a scheduled request after lifecycle prerequisites are met."""
        if request.status != ChangeStatus.SCHEDULED.value:
            raise ValueError("only scheduled changes can enter execution")
        request.status = ChangeStatus.IN_PROGRESS.value
        request.updated_at = datetime.now(timezone.utc)
        return self.summary(request)

    def update_step(self, request: ChangeRequest, step_number: int, step_status: str, *, executed_by: str, actual_output: str = "", matches_expected: bool | None = None, notes: str = "") -> ExecutionSummary:
        """Append a redacted step event and update the request status."""
        if step_status not in {item.value for item in StepStatus}:
            raise ValueError("unsupported step status")
        if step_number < 1 or step_number > len(request.implementation_plan.steps):
            raise ValueError("step number is outside implementation plan")
        if not executed_by:
            raise ValueError("executed_by is required")
        now = datetime.now(timezone.utc)
        started = now if step_status == StepStatus.IN_PROGRESS.value else None
        completed = now if step_status in {StepStatus.COMPLETED.value, StepStatus.FAILED.value, StepStatus.SKIPPED.value} else None
        redacted = RedactingFilter.sanitize_value(actual_output)
        output = redacted if isinstance(redacted, str) else str(redacted)
        event = ExecutionEvent(f"{request.change_id}:execution:{len(request.execution_log) + 1:04d}", step_number, step_status, started, completed, executed_by, output, matches_expected, notes)
        request.execution_log.append(event)
        request.updated_at = now
        if step_status == StepStatus.FAILED.value:
            request.status = ChangeStatus.FAILED.value
        elif all(item.step_number in {event_item.step_number for event_item in request.execution_log if event_item.step_status == StepStatus.COMPLETED.value} for item in request.implementation_plan.steps):
            request.status = ChangeStatus.VERIFICATION.value
        else:
            request.status = ChangeStatus.IN_PROGRESS.value
        return self.summary(request)

    def summary(self, request: ChangeRequest) -> ExecutionSummary:
        """Calculate current execution summary."""
        completed = {event.step_number for event in request.execution_log if event.step_status == StepStatus.COMPLETED.value}
        failed = any(event.step_status == StepStatus.FAILED.value for event in request.execution_log)
        status = ExecutionStatus.FAILED.value if failed else ExecutionStatus.COMPLETED.value if request.status == ChangeStatus.VERIFICATION.value else ExecutionStatus.IN_PROGRESS.value if request.execution_log else ExecutionStatus.NOT_STARTED.value
        current = max((event.step_number for event in request.execution_log), default=0)
        started_times = [event.started_at for event in request.execution_log if event.started_at]
        started = min(started_times) if started_times else None
        elapsed = max(0.0, (datetime.now(timezone.utc) - started).total_seconds()) if started else 0.0
        remaining = None
        if request.implementation_plan.estimated_duration.total_seconds() > 0:
            remaining = max(0.0, request.implementation_plan.estimated_duration.total_seconds() - elapsed)
        return ExecutionSummary(status, current, len(completed), len(request.implementation_plan.steps), started, elapsed, remaining)
