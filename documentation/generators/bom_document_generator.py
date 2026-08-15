"""Generator for the Bill of Materials artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class BOMDocumentGenerator(BaseDocumentGenerator):
    """Generate Bill of Materials from resolved source artifacts."""

    document_type = DocumentType.BOM
    title_en = "Bill of Materials"
    title_ar = "جدول المواد"
