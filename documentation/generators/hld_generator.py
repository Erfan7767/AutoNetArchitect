"""Generator for the High-Level Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class HLDGenerator(BaseDocumentGenerator):
    """Generate High-Level Design Document from resolved source artifacts."""

    document_type = DocumentType.HLD
    title_en = "High-Level Design Document"
    title_ar = "وثيقة التصميم عالي المستوى"
