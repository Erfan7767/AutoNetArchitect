"""Generator for the Troubleshooting Guide artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class TroubleshootingGuideGenerator(BaseDocumentGenerator):
    """Generate Troubleshooting Guide from resolved source artifacts."""

    document_type = DocumentType.TROUBLESHOOTING_GUIDE
    title_en = "Troubleshooting Guide"
    title_ar = "دليل استكشاف الأخطاء"
