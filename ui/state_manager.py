"""Local single-user UI state, project locking, and secret-safe presentation helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid
from typing import Any, Mapping

from log_redaction.redacting_filter import RedactingFilter


class UIStateError(RuntimeError):
    """Base error for local UI state operations."""


class ProjectLockError(UIStateError):
    """Raised when a local project lock cannot be acquired or released safely."""


@dataclass
class UIState:
    """Persisted UI state for one local user and one selected project."""

    project_id: str | None = None
    actor: str | None = None
    active_page: str = "01_questionnaire"
    workflow_context: dict[str, Any] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    approval_requests: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize state using only JSON-compatible values."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "UIState":
        """Build state from a trusted local JSON mapping."""
        if not isinstance(payload, Mapping):
            raise UIStateError("UI state must be a mapping")
        return cls(
            project_id=str(payload["project_id"]) if payload.get("project_id") is not None else None,
            actor=str(payload["actor"]) if payload.get("actor") is not None else None,
            active_page=str(payload.get("active_page", "01_questionnaire")),
            workflow_context=dict(payload.get("workflow_context", {})),
            values=dict(payload.get("values", {})),
            notifications=[dict(item) for item in payload.get("notifications", [])],
            approval_requests=[dict(item) for item in payload.get("approval_requests", [])],
            updated_at=str(payload.get("updated_at", datetime.now(timezone.utc).isoformat())),
            version=int(payload.get("version", 1)),
        )


class ProjectLock:
    """Exclusive local project lock that never silently steals another lock."""

    def __init__(self, path: str | Path, *, actor: str, project_id: str) -> None:
        """Create a lock handle with explicit actor and project identity."""
        if not actor or not project_id:
            raise ValueError("actor and project_id are required")
        self.path = Path(path)
        self.actor = actor
        self.project_id = project_id
        self.token = f"lock:{uuid.uuid4()}"
        self._acquired = False

    def acquire(self) -> None:
        """Acquire the lock atomically or raise without modifying an existing lock."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "token": self.token,
            "pid": os.getpid(),
            "actor": self.actor,
            "project_id": self.project_id,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }
        encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ProjectLockError(f"project lock already exists: {self.path}") from exc
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
        except Exception:
            self.path.unlink(missing_ok=True)
            raise
        self._acquired = True

    def release(self) -> None:
        """Release only the lock owned by this handle."""
        if not self._acquired:
            return
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self._acquired = False
            raise ProjectLockError("project lock metadata is missing or invalid") from exc
        if current.get("token") != self.token:
            self._acquired = False
            raise ProjectLockError("project lock ownership changed; refusing unsafe release")
        self.path.unlink(missing_ok=True)
        self._acquired = False

    def is_held(self) -> bool:
        """Return whether this handle still owns the lock."""
        if not self._acquired or not self.path.exists():
            return False
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return current.get("token") == self.token

    def __enter__(self) -> "ProjectLock":
        """Acquire the lock for a context-managed UI action."""
        self.acquire()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Any) -> None:
        """Release the lock after a context-managed action."""
        self.release()


class UIStateManager:
    """Persist and update UI state using local atomic writes."""

    def __init__(self, path: str | Path, *, lock_path: str | Path | None = None) -> None:
        """Create a state manager backed by one JSON file."""
        self.path = Path(path)
        self.lock_path = Path(lock_path) if lock_path is not None else self.path.with_suffix(self.path.suffix + ".lock")
        self._state = self._load()

    def snapshot(self) -> UIState:
        """Return a detached copy of current state."""
        return UIState.from_dict(self._state.to_dict())

    def set_project(self, project_id: str, actor: str) -> UIState:
        """Select the local project and actor for the UI session."""
        if not project_id or not actor:
            raise UIStateError("project_id and actor are required")
        self._state.project_id = project_id
        self._state.actor = actor
        return self.save()

    def set_page(self, page_name: str) -> UIState:
        """Update the active page label."""
        if not page_name or "/" in page_name or "\\" in page_name:
            raise UIStateError("page name must be a simple non-empty label")
        self._state.active_page = page_name
        return self.save()

    def update_values(self, values: Mapping[str, Any]) -> UIState:
        """Merge UI values after recursively masking sensitive fields for persistence."""
        if not isinstance(values, Mapping):
            raise UIStateError("UI values must be a mapping")
        sanitized = RedactingFilter.sanitize_value(dict(values))
        if not isinstance(sanitized, dict):
            raise UIStateError("sanitized UI values must remain a mapping")
        self._state.values.update(sanitized)
        return self.save()

    def set_workflow_context(self, context: Mapping[str, Any]) -> UIState:
        """Store an orchestrator context without raw secret values."""
        sanitized = RedactingFilter.sanitize_value(dict(context))
        if not isinstance(sanitized, dict):
            raise UIStateError("workflow context must remain a mapping")
        self._state.workflow_context = sanitized
        return self.save()

    def add_notification(self, level: str, message: str, *, details: Mapping[str, Any] | None = None) -> UIState:
        """Add a secret-safe user notification."""
        if level not in {"info", "success", "warning", "error", "blocked"}:
            raise UIStateError("unsupported notification level")
        if not message:
            raise UIStateError("notification message is required")
        self._state.notifications.append({"level": level, "message": RedactingFilter.redact_text(message), "details": RedactingFilter.sanitize_value(dict(details or {})), "created_at": datetime.now(timezone.utc).isoformat()})
        self._state.notifications = self._state.notifications[-100:]
        return self.save()

    def add_approval_request(self, *, action: str, stage: str, reasons: tuple[str, ...], required_role: str = "engineer") -> UIState:
        """Persist a visible approval request without permitting approval itself."""
        if not action or not stage or not required_role:
            raise UIStateError("action, stage, and required_role are required")
        self._state.approval_requests.append({"request_id": f"ui-approval:{uuid.uuid4()}", "action": action, "stage": stage, "reasons": list(reasons), "required_role": required_role, "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()})
        return self.save()

    def save(self) -> UIState:
        """Atomically persist state and increment the local version."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._state.updated_at = datetime.now(timezone.utc).isoformat()
        self._state.version += 1
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self._state.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return self.snapshot()

    def lock(self, *, actor: str | None = None, project_id: str | None = None) -> ProjectLock:
        """Create a lock for the selected project without acquiring it."""
        effective_actor = actor or self._state.actor
        effective_project = project_id or self._state.project_id
        if not effective_actor or not effective_project:
            raise ProjectLockError("a selected project and actor are required before locking")
        return ProjectLock(self.lock_path, actor=effective_actor, project_id=effective_project)

    def _load(self) -> UIState:
        """Load state or create an empty local state."""
        if not self.path.exists():
            return UIState()
        try:
            return UIState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, UIStateError, TypeError, ValueError) as exc:
            raise UIStateError(f"cannot load UI state: {exc}") from exc


def mask_for_ui(value: Any) -> Any:
    """Return a recursively sanitized value suitable for display in the UI."""
    return RedactingFilter.sanitize_value(value)
