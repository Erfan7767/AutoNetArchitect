"""PDF renderer with bilingual-safe metadata and tables."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFRenderer:
    """Render a readable PDF and register Arabic font when available."""

    def __init__(self) -> None:
        """Register local font if present."""
        self.font_name = "Helvetica"
        font_path = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont("NotoSansArabic", font_path))
                self.font_name = "NotoSansArabic"
            except (OSError, ValueError):
                self.font_name = "Helvetica"

    def render(self, content: dict[str, Any], output_path: str, *, watermark: str = "DRAFT") -> int:
        """Write a PDF containing headings, statuses, and JSON-safe content."""
        document = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title=str(content.get("title_en", "Document")))
        styles = getSampleStyleSheet()
        heading = ParagraphStyle("DocHeading", parent=styles["Heading2"], fontName=self.font_name, alignment=TA_LEFT, spaceBefore=8, spaceAfter=5)
        body = ParagraphStyle("DocBody", parent=styles["BodyText"], fontName=self.font_name, leading=13)
        story = [Paragraph(f"{content.get('title_en', 'Document')} / {content.get('title_ar', '')}", ParagraphStyle("Title", parent=styles["Title"], fontName=self.font_name)), Paragraph(f"Watermark: {watermark or 'NONE'} | Generated: {content.get('generated_at', 'PENDING')}", body), Spacer(1, 8)]
        for section in content.get("sections", []):
            story.append(Paragraph(f"{section.get('title_en', '')} / {section.get('title_ar', '')}", heading))
            story.append(Paragraph(f"Status: {section.get('status', 'pending')}", body))
            value = section.get("content")
            if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                headers = sorted({str(key) for item in value for key in item.keys()})
                rows = [headers] + [[str(item.get(key, "")) for key in headers] for item in value]
                table = Table(rows, repeatRows=1)
                table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 7)]))
                story.append(table)
            else:
                story.append(Paragraph(json.dumps(value, ensure_ascii=False, default=str), body))
        document.build(story)
        return max(1, len(content.get("sections", [])) + 1)
