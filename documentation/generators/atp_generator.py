"""Generator for the Acceptance Test Procedure artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class ATPGenerator(BaseDocumentGenerator):
    """Generate Acceptance Test Procedure from resolved source artifacts."""

    document_type = DocumentType.ATP
    title_en = "Acceptance Test Procedure"
    title_ar = "إجراء اختبار القبول"
