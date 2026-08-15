"""Header and footer metadata helpers."""
from __future__ import annotations

from typing import Any


class HeaderFooterFormatter:
    """Create consistent document header and footer records."""

    def build(self, *, title: str, revision: str = "1.0", confidential: bool = False) -> dict[str, Any]:
        """Return header/footer values for a renderer."""
        return {"header": title, "revision": revision, "footer": "CONFIDENTIAL" if confidential else "Generated documentation", "page_number": True}
