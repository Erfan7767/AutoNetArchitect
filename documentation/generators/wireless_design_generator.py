"""Generator for the Wireless Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class WirelessDesignGenerator(BaseDocumentGenerator):
    """Generate Wireless Design Document from resolved source artifacts."""

    document_type = DocumentType.WIRELESS_DESIGN
    title_en = "Wireless Design Document"
    title_ar = "وثيقة تصميم الشبكة اللاسلكية"
