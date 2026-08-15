"""Contract tests for repository EditorConfig policy."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EDITORCONFIG = PROJECT_ROOT / ".editorconfig"


def _editorconfig_text() -> str:
    """Return the repository EditorConfig text."""
    return EDITORCONFIG.read_text(encoding="utf-8")


def test_editorconfig_declares_root_and_global_defaults() -> None:
    """Ensure every editor starts from the same encoding and newline policy."""
    text = _editorconfig_text()
    assert "root = true" in text
    assert "indent_style = space" in text
    assert "indent_size = 4" in text
    assert "end_of_line = lf" in text
    assert "charset = utf-8" in text
    assert "trim_trailing_whitespace = true" in text
    assert "insert_final_newline = true" in text


def test_editorconfig_declares_language_specific_overrides() -> None:
    """Ensure the supplied file-type overrides are present and bounded."""
    text = _editorconfig_text()
    assert "[*.py]" in text
    assert "max_line_length = 120" in text
    assert "[*.{yml,yaml}]" in text
    assert "[*.{json}]" in text
    assert "[*.j2]" in text
    assert "[*.md]" in text
    assert "trim_trailing_whitespace = false" in text


def test_editorconfig_preserves_makefile_and_script_indentation() -> None:
    """Ensure Make recipes retain tabs and shell files retain explicit spacing."""
    text = _editorconfig_text()
    assert "[Makefile]" in text
    assert "indent_style = tab" in text
    assert "[*.sh]" in text
    assert "indent_size = 2" in text
