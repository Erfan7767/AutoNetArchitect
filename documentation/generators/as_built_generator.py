"""Generator for the As-Built Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class AsBuiltGenerator(BaseDocumentGenerator):
    """Generate As-Built Document from resolved source artifacts."""

    document_type = DocumentType.AS_BUILT
    title_en = "As-Built Document"
    title_ar = "وثيقة الحالة المنفذة"
