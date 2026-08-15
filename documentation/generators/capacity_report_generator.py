"""Generator for the Capacity Planning Report artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class CapacityReportGenerator(BaseDocumentGenerator):
    """Generate Capacity Planning Report from resolved source artifacts."""

    document_type = DocumentType.CAPACITY_REPORT
    title_en = "Capacity Planning Report"
    title_ar = "تقرير تخطيط السعة"
