"""Generator for the WAN Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class WANDesignGenerator(BaseDocumentGenerator):
    """Generate WAN Design Document from resolved source artifacts."""

    document_type = DocumentType.WAN_DESIGN
    title_en = "WAN Design Document"
    title_ar = "وثيقة تصميم WAN"
