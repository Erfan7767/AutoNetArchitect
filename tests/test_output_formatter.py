"""Tests for CLI output formatting."""
from __future__ import annotations

from cli.output_formatter import OutputFormatter


def test_output_formatter_json_masks_secrets():
    rendered = OutputFormatter("json", no_color=True).render({"token": "raw", "status": "ok"}, status="success", message="done")
    assert '"token": "<REDACTED>"' in rendered


def test_output_formatter_yaml_and_table_are_structured():
    yaml_output = OutputFormatter("yaml", no_color=True).render({"items": ["a", "b"]})
    table_output = OutputFormatter("table", no_color=True).render([{"name": "one", "status": "ok"}])
    assert "items:" in yaml_output
    assert "name" in table_output
    assert "+" in table_output


def test_output_formatter_quiet_suppresses_success():
    assert OutputFormatter("text", no_color=True, quiet=True).render({"ok": True}, status="success", message="done") == ""
