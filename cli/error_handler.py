"""User-facing CLI error mapping and exit-code policy."""
from __future__ import annotations

from dataclasses import dataclass
import traceback
from typing import Any

from auth.auth_manager import AuthenticationError
from auth.rbac import PermissionDenied
from auth.session_manager import SessionError


@dataclass(frozen=True)
class CLIError:
    """Safe error representation with a stable process exit code."""

    message: str
    exit_code: int
    category: str
    details: dict[str, Any]
    debug_trace: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error without exposing credential values."""
        return {"message": self.message, "exit_code": self.exit_code, "category": self.category, "details": dict(self.details), "debug_trace": self.debug_trace}


class ErrorHandler:
    """Convert known CLI and domain errors to stable user-facing outcomes."""

    def classify(self, error: BaseException, *, debug: bool = False) -> CLIError:
        """Map an exception to the requested exit-code taxonomy."""
        if isinstance(error, (AuthenticationError, SessionError, PermissionDenied)):
            category, code = "authentication", 3
        elif isinstance(error, (ValueError, TypeError)):
            category, code = "input_validation", 2
        elif isinstance(error, FileNotFoundError):
            category, code = "project_not_found", 4
        elif isinstance(error, PermissionError):
            category, code = "governance_blocked", 5
        elif getattr(error, "__class__", None).__name__ in {"DeploymentError", "DeploymentFailure"}:
            category, code = "deployment_failed", 6
        else:
            category, code = "internal", 10
        return CLIError(str(error), code, category, {"exception_type": type(error).__name__}, traceback.format_exc() if debug else None)

    def render(self, error: BaseException, *, debug: bool = False) -> str:
        """Render one friendly error string."""
        classified = self.classify(error, debug=debug)
        lines = [f"Error [{classified.category}] (exit {classified.exit_code}): {classified.message}"]
        if debug and classified.debug_trace:
            lines.append(classified.debug_trace)
        return "\n".join(lines)
