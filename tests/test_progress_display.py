"""Tests for CLI progress display."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

from cli.progress_display import ProgressDisplay


def test_progress_steps_and_spinner_emit_deterministic_markers():
    display = ProgressDisplay(enabled=True)
    buffer = StringIO()
    with redirect_stdout(buffer):
        assert display.steps("check", [1, 2]) == [1, 2]
        marker = []
        with display.spinner("load"):
            marker.append("entered")
    captured = buffer.getvalue()
    assert marker == ["entered"]
    assert "check 1/2" in captured
    assert "load complete" in captured
