"""Generator for the Technical Compliance Assessment Report artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class ComplianceReportGenerator(BaseDocumentGenerator):
    """Generate Technical Compliance Assessment Report from resolved source artifacts."""

    document_type = DocumentType.COMPLIANCE_REPORT
    title_en = "Technical Compliance Assessment Report"
    title_ar = "تقرير تقييم الامتثال التقني"
