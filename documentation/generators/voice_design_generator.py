"""Generator for the Voice and UC Network Design artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class VoiceDesignGenerator(BaseDocumentGenerator):
    """Generate Voice and UC Network Design from resolved source artifacts."""

    document_type = DocumentType.VOICE_DESIGN
    title_en = "Voice and UC Network Design"
    title_ar = "تصميم شبكة الصوت والاتصالات الموحدة"
