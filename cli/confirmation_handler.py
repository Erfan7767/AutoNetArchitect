"""Confirmation policies for safe CLI actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ConfirmationPolicy:
    """Describe one confirmation requirement."""

    prompt: str
    required_text: str | None = None
    mandatory: bool = False


class ConfirmationHandler:
    """Implement explicit confirmations with injectable input."""

    def __init__(self, *, input_fn: Callable[[str], str] = input) -> None:
        """Create a confirmation handler."""
        self.input_fn = input_fn

    def confirm(self, policy: ConfirmationPolicy, *, yes: bool = False) -> bool:
        """Return whether the user confirmed an action."""
        if yes and policy.mandatory:
            raise PermissionError("mandatory confirmation cannot be skipped with --yes")
        if yes:
            return True
        response = self.input_fn(f"{policy.prompt} [y/N]: ").strip().lower()
        return response in {"y", "yes"}

    def typed(self, policy: ConfirmationPolicy, *, supplied: str | None = None) -> bool:
        """Require an exact typed confirmation string."""
        if not policy.required_text:
            raise ValueError("typed confirmation requires required_text")
        response = supplied if supplied is not None else self.input_fn(f"{policy.prompt}: ")
        return response == policy.required_text

    def multi_step(self, summary: str, *, yes: bool = False, mandatory: bool = True) -> bool:
        """Apply summary and typed deployment confirmation."""
        first = self.confirm(ConfirmationPolicy(summary, mandatory=mandatory), yes=yes)
        if not first:
            return False
        if yes:
            if mandatory:
                raise PermissionError("typed deployment confirmation is required")
            return True
        return self.typed(ConfirmationPolicy("Type DEPLOY to confirm", required_text="DEPLOY", mandatory=mandatory))
