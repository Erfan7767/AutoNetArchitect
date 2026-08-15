"""Arabic and bilingual document formatting helpers."""
from __future__ import annotations

from datetime import datetime

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None


class ArabicFormatter:
    """Provide optional shaping and RTL metadata without changing source facts."""

    def format_text(self, text: str, *, shape: bool = True) -> str:
        """Shape Arabic text when optional rendering dependencies are installed."""
        if not shape or arabic_reshaper is None or get_display is None:
            return text
        return get_display(arabic_reshaper.reshape(text))

    def bilingual_header(self, english: str, arabic: str) -> str:
        """Return an explicit bilingual heading."""
        return f"{english} / {self.format_text(arabic)}"

    def date_text(self, value: datetime) -> str:
        """Format an ISO date with an Arabic calendar label while retaining ISO value."""
        return f"{value.date().isoformat()} / التاريخ"

    def rtl_attributes(self) -> dict[str, str]:
        """Return metadata consumed by HTML and Word renderers."""
        return {"dir": "rtl", "lang": "ar", "font": "Noto Sans Arabic"}
