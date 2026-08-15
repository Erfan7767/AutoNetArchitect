"""Dependency-light Word-compatible OOXML renderer."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


class WordRenderer:
    """Create an editable .docx package without relying on python-docx."""

    def render(self, content: dict[str, Any], output_path: str, *, watermark: str = "DRAFT") -> int:
        """Write minimal valid WordprocessingML with headings and paragraphs."""
        body: list[str] = []
        body.append(self._paragraph(f"{content.get('title_en', 'Document')} / {content.get('title_ar', '')}", style="Title"))
        body.append(self._paragraph(f"Watermark: {watermark or 'NONE'} | Generated: {content.get('generated_at', 'PENDING')}"))
        for section in content.get("sections", []):
            level = min(max(int(section.get("level", 1)), 1), 3)
            body.append(self._paragraph(f"{section.get('title_en', '')} / {section.get('title_ar', '')}", style=f"Heading{level}"))
            body.append(self._paragraph(f"Status: {section.get('status', 'pending')}"))
            body.append(self._paragraph(str(section.get("content"))))
        document_xml = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body>" + "".join(body) + "<w:sectPr><w:pgSz w:w='11906' w:h='16838'/><w:pgMar w:top='1440' w:right='1440' w:bottom='1440' w:left='1440'/></w:sectPr></w:body></w:document>"
        content_types = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/></Types>"
        rels = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/></Relationships>"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", rels)
            archive.writestr("word/document.xml", document_xml)
        return max(1, len(content.get("sections", [])) + 1)

    @staticmethod
    def _paragraph(text: str, *, style: str | None = None) -> str:
        """Build a Word paragraph with escaped UTF-8 text."""
        properties = f"<w:pPr><w:pStyle w:val='{escape(style)}'/></w:pPr>" if style else ""
        return f"<w:p>{properties}<w:r><w:t xml:space='preserve'>{escape(text)}</w:t></w:r></w:p>"
