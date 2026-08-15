"""Tests for CLI confirmation policy."""
from __future__ import annotations

from collections import deque

from cli.confirmation_handler import ConfirmationHandler, ConfirmationPolicy


def test_confirmation_yes_and_typed_paths():
    handler = ConfirmationHandler(input_fn=lambda _prompt: "y")
    assert handler.confirm(ConfirmationPolicy("Proceed"), yes=True) is True
    assert handler.typed(ConfirmationPolicy("Type", required_text="DEPLOY"), supplied="DEPLOY") is True


def test_mandatory_confirmation_cannot_use_yes():
    handler = ConfirmationHandler(input_fn=lambda _prompt: "y")
    blocked = False
    try:
        handler.confirm(ConfirmationPolicy("Destroy", mandatory=True), yes=True)
    except PermissionError:
        blocked = True
    if not blocked:
        raise AssertionError("mandatory confirmation should not be bypassed")


def test_multi_step_requires_exact_deploy_text():
    answers = deque(["y", "DEPLOY"])
    handler = ConfirmationHandler(input_fn=lambda _prompt: answers.popleft())
    assert handler.multi_step("Deploy now", yes=False, mandatory=True) is True
