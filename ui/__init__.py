"""Minimal, local, secret-safe V1 UI shell for AutoNetArchitect."""

from .app import AppShell, PageResponse, UIController, create_app
from .background_jobs import BackgroundJobManager, JobRecord, JobStatus
from .state_manager import ProjectLock, ProjectLockError, UIState, UIStateError, UIStateManager, mask_for_ui

__all__ = [
    "AppShell",
    "BackgroundJobManager",
    "JobRecord",
    "JobStatus",
    "PageResponse",
    "ProjectLock",
    "ProjectLockError",
    "UIController",
    "UIState",
    "UIStateError",
    "UIStateManager",
    "create_app",
    "mask_for_ui",
]
