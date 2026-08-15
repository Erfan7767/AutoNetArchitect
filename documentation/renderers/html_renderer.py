"""HTML renderer for structured documentation."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class HTMLRenderer:
    """Render a self-contained HTML document with bilingual headings."""

    def render(self, content: dict[str, Any], output_path: str, *, watermark: str = "DRAFT") -> int:
        """Write HTML and return an estimated page count."""
        blocks = [f"<h1>{html.escape(str(content.get('title_en', 'Document')))} / {html.escape(str(content.get('title_ar', '')))}</h1>", f"<p><strong>Watermark:</strong> {html.escape(watermark or 'NONE')}</p>", f"<p><strong>Generated:</strong> {html.escape(str(content.get('generated_at', 'PENDING')))}</p>"]
        for section in content.get("sections", []):
            tag = f"h{min(max(int(section.get('level', 1)) + 1, 2), 4)}"
            blocks.append(f"<{tag}>{html.escape(str(section.get('title_en', '')))} / {html.escape(str(section.get('title_ar', '')))}</{tag}>")
            blocks.append(f"<p><strong>Status:</strong> {html.escape(str(section.get('status', 'pending')))}</p>")
            blocks.append(f"<pre>{html.escape(json.dumps(section.get('content'), ensure_ascii=False, indent=2, default=str))}</pre>")
        document = "<!doctype html><html lang='en'><head><meta charset='utf-8'><style>body{font-family:Arial,'Noto Sans Arabic',sans-serif;margin:2rem;line-height:1.5}pre{white-space:pre-wrap;background:#f4f4f4;padding:1rem}</style></head><body>" + "".join(blocks) + "</body></html>"
        Path(output_path).write_text(document, encoding="utf-8")
        return max(1, len(blocks) // 6)
