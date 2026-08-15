"""Bilingual, Arabic-capable PDF report generator."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping, Sequence
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ._common import localized, metadata, safe_json, sanitize, write_text
from .report_models import ReportArtifact, ReportLanguage

class PDFGenerator:
    """Generate secret-safe PDF reports with Arabic font support."""
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
    FONT_NAME = "AutoNetArchitectArabic"
    def __init__(self) -> None:
        """Register the available Arabic-capable font once."""
        if self.FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            if not Path(self.FONT_PATH).exists():
                raise FileNotFoundError(f"Arabic font not found: {self.FONT_PATH}")
            pdfmetrics.registerFont(TTFont(self.FONT_NAME, self.FONT_PATH))
    @staticmethod
    def _shape(text: str) -> str:
        """Shape Arabic text when the optional shaping libraries are available."""
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    def generate(self, *, title: str, sections: Mapping[str, Any], output_path: str | Path, language: ReportLanguage | str = ReportLanguage.BOTH, sot_basis: Mapping[str, str] | None = None, evidence_basis: Sequence[str] = ()) -> ReportArtifact:
        """Generate a PDF with metadata, localized title, SoT basis, and redacted sections."""
        selected = ReportLanguage(language)
        meta = metadata(title=title, language=selected, sot_basis=sot_basis, evidence_basis=evidence_basis, disclaimer="Technical report generated from supplied records. It is not a certification, audit opinion, or production-safety claim.")
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        y = height - 42
        pdf.setFont(self.FONT_NAME, 12)
        lines = [localized(selected, title, title), f"Report ID: {meta.report_id}", f"Generated at: {meta.generated_at.isoformat()}", f"SoT basis: {meta.sot_basis or {'status': 'not supplied'}}", f"Evidence basis: {meta.evidence_basis or ['none supplied']}", meta.disclaimer]
        for key, value in sections.items():
            lines.append(f"{key}: {safe_json(value).strip()}")
        for raw in lines:
            for line in str(raw).splitlines() or [""]:
                if y < 42:
                    pdf.showPage(); pdf.setFont(self.FONT_NAME, 12); y = height - 42
                pdf.drawString(36, y, self._shape(line[:180])); y -= 16
        pdf.save()
        return ReportArtifact(metadata=meta, output_path=str(target), format="pdf")
