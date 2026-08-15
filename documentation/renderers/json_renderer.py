"""JSON renderer for machine-readable documentation artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JSONRenderer:
    """Write structured content as UTF-8 JSON."""

    def render(self, content: dict[str, Any], output_path: str, *, watermark: str = "DRAFT") -> int:
        """Write JSON with deterministic formatting."""
        output = dict(content)
        output["watermark"] = watermark or "NONE"
        Path(output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str) + "\\n", encoding="utf-8")
        return 1
