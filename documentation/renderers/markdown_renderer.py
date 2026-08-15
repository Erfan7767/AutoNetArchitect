"""Markdown renderer for structured documentation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..formatters.table_formatter import TableFormatter


class MarkdownRenderer:
    """Render bilingual structured content as readable Markdown."""

    def render(self, content: dict[str, Any], output_path: str, *, watermark: str = "DRAFT") -> int:
        """Write Markdown and return an estimated page count."""
        lines = [f"# {content.get('title_en', 'Document')} / {content.get('title_ar', '')}", "", f"**Watermark:** {watermark or 'NONE'}", f"**Generated:** {content.get('generated_at', 'PENDING')}", f"**Schema:** {content.get('schema_version', '1.0')}", f"**Completeness:** {content.get('completeness_score', 0)}%", "", "> Generated from supplied source artifacts only.", ""]
        for section in content.get("sections", []):
            level = min(max(int(section.get("level", 1)) + 1, 2), 4)
            lines.extend(["#" * level + " " + f"{section.get('title_en', '')} / {section.get('title_ar', '')}", f"**Status:** {section.get('status', 'pending')}", ""])
            value = section.get("content")
            if isinstance(value, (dict, list)):
                lines.append(TableFormatter().markdown(value))
            else:
                lines.append(str(value))
            lines.append("")
        Path(output_path).write_text("\\n".join(lines), encoding="utf-8")
        return max(1, len(lines) // 45)

    def to_string(self, content: dict[str, Any]) -> str:
        """Return Markdown without writing a file."""
        path = Path('/tmp/documentation-markdown-output.md')
        self.render(content, str(path), watermark="NONE")
        return path.read_text(encoding="utf-8")
