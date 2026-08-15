"""Minimal valid DOCX generator with Arabic RTL metadata."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping, Sequence
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape
from ._common import localized, metadata, safe_json
from .report_models import ReportArtifact, ReportLanguage

class WordGenerator:
    """Generate a self-contained DOCX without exposing secret values."""
    def generate(self, *, title: str, sections: Mapping[str, Any], output_path: str | Path, language: ReportLanguage | str = ReportLanguage.BOTH, sot_basis: Mapping[str, str] | None = None, evidence_basis: Sequence[str] = ()) -> ReportArtifact:
        """Write a minimal Office Open XML document with bilingual content."""
        selected = ReportLanguage(language)
        meta = metadata(title=title, language=selected, sot_basis=sot_basis, evidence_basis=evidence_basis)
        target = Path(output_path); target.parent.mkdir(parents=True, exist_ok=True)
        paragraphs = [localized(selected, title, title), f"Report ID: {meta.report_id}", f"Generated at: {meta.generated_at.isoformat()}", f"SoT basis: {meta.sot_basis or {'status': 'not supplied'}}", f"Evidence basis: {meta.evidence_basis or ['none supplied']}", meta.disclaimer]
        for key, value in sections.items(): paragraphs.append(f"{key}: {safe_json(value).strip()}")
        document_body = "".join(self._paragraph(item, selected) for item in paragraphs)
        document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{document_body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>"""
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>"""
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"""
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", rels)
            archive.writestr("word/document.xml", document)
        return ReportArtifact(metadata=meta, output_path=str(target), format="docx")
    @staticmethod
    def _paragraph(text: str, language: ReportLanguage) -> str:
        """Build one paragraph with RTL properties for Arabic modes."""
        escaped = escape(text)
        rtl = "<w:rtl/>" if language in {ReportLanguage.ARABIC, ReportLanguage.BOTH} else ""
        fonts = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Noto Naskh Arabic"/>'
        return f'<w:p><w:pPr>{rtl}</w:pPr><w:r><w:rPr>{fonts}</w:rPr><w:t xml:space="preserve">{escaped}</w:t></w:r></w:p>'
