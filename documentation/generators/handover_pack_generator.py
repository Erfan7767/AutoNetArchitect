"""Generator for the Project Handover Package artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class HandoverPackGenerator(BaseDocumentGenerator):
    """Generate Project Handover Package from resolved source artifacts."""

    document_type = DocumentType.HANDOVER_PACK
    title_en = "Project Handover Package"
    title_ar = "حزمة تسليم المشروع"
