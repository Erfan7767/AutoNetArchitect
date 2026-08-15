"""Tests for CLI error handling."""
from __future__ import annotations

from auth.auth_manager import AuthenticationError
from cli.error_handler import ErrorHandler


def test_error_handler_maps_known_error_codes():
    handler = ErrorHandler()
    assert handler.classify(AuthenticationError("bad"), debug=False).exit_code == 3
    assert handler.classify(ValueError("bad input"), debug=False).exit_code == 2
    assert handler.classify(FileNotFoundError("missing"), debug=False).exit_code == 4
    assert handler.classify(PermissionError("blocked"), debug=False).exit_code == 5


def test_error_handler_hides_trace_without_debug_and_includes_with_debug():
    handler = ErrorHandler()
    no_debug = handler.classify(RuntimeError("internal"), debug=False)
    with_debug = handler.classify(RuntimeError("internal"), debug=True)
    assert no_debug.debug_trace is None
    assert with_debug.debug_trace is not None
