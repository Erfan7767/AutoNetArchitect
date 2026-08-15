"""Generator for the Low-Level Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class LLDGenerator(BaseDocumentGenerator):
    """Generate Low-Level Design Document from resolved source artifacts."""

    document_type = DocumentType.LLD
    title_en = "Low-Level Design Document"
    title_ar = "وثيقة التصميم منخفض المستوى"
