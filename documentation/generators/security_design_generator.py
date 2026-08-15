"""Generator for the Security Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class SecurityDesignGenerator(BaseDocumentGenerator):
    """Generate Security Design Document from resolved source artifacts."""

    document_type = DocumentType.SECURITY_DESIGN
    title_en = "Security Design Document"
    title_ar = "وثيقة التصميم الأمني"
