"""Table of contents generation."""
from __future__ import annotations

from typing import Any


class TOCGenerator:
    """Build a table of contents from structured section records."""

    def generate(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        """Return section identifiers, bilingual titles, and levels."""
        return [{"section_id": item.get("section_id", ""), "title_en": item.get("title_en", ""), "title_ar": item.get("title_ar", ""), "level": item.get("level", 1)} for item in content.get("sections", [])]
