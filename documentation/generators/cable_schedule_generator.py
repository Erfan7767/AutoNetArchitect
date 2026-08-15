"""Generator for the Cable Schedule artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class CableScheduleGenerator(BaseDocumentGenerator):
    """Generate Cable Schedule from resolved source artifacts."""

    document_type = DocumentType.CABLE_SCHEDULE
    title_en = "Cable Schedule"
    title_ar = "جدول الكابلات"
