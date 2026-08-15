"""Generator for the QoS Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class QoSDesignGenerator(BaseDocumentGenerator):
    """Generate QoS Design Document from resolved source artifacts."""

    document_type = DocumentType.QOS_DESIGN
    title_en = "QoS Design Document"
    title_ar = "وثيقة تصميم جودة الخدمة"
