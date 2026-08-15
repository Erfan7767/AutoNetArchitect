"""Shared generator contract for every engineering document."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..doc_models import DocumentType, Language, ResolvedData, SectionStatus


class BaseDocumentGenerator:
    """Build structured document content from resolved source artifacts."""

    document_type: DocumentType
    title_en: str = "Network Engineering Document"
    title_ar: str = "وثيقة هندسة الشبكات"

    def generate(self, resolved: ResolvedData, *, language: Language | str = Language.BILINGUAL) -> dict[str, Any]:
        """Generate a complete structured content object without fabricating values."""
        selected_language = Language(language)
        if resolved.document_type != self.document_type:
            raise ValueError(f"generator {self.document_type.value} received {resolved.document_type.value}")
        sections: list[dict[str, Any]] = []
        for item in resolved.sections:
            section_content = item.content if item.has_content else f"PENDING: {item.pending_reason or 'source data not supplied'}"
            sections.append({
                "section_id": item.section.section_id,
                "title_en": item.section.section_title_en,
                "title_ar": item.section.section_title_ar,
                "level": item.section.section_level,
                "content_type": item.section.content_type.value,
                "status": item.status.value,
                "mandatory": item.section.mandatory,
                "pending_reason": item.pending_reason,
                "content": section_content,
                "source_artifacts": item.source_artifacts,
                "assumptions": item.assumptions,
            })
        return {
            "document_type": self.document_type.value,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "language": selected_language.value,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0",
            "sot_basis": resolved.sot_basis,
            "evidence_basis": resolved.evidence_basis,
            "completeness_score": resolved.completeness_score,
            "pending_sections": resolved.pending_sections,
            "stale_sections": resolved.stale_sections,
            "assumptions": resolved.assumptions,
            "disclaimer": "Generated only from supplied source artifacts; PENDING identifies unavailable inputs.",
            "sections": sections,
        }
