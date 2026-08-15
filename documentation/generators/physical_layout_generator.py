"""Generator for the Physical Layout Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class PhysicalLayoutGenerator(BaseDocumentGenerator):
    """Generate Physical Layout Document from resolved source artifacts."""

    document_type = DocumentType.PHYSICAL_LAYOUT
    title_en = "Physical Layout Document"
    title_ar = "وثيقة المخطط الفيزيائي"
