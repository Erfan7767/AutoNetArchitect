"""Generator for the Operational Runbook artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class OperationalRunbookGenerator(BaseDocumentGenerator):
    """Generate Operational Runbook from resolved source artifacts."""

    document_type = DocumentType.OPERATIONAL_RUNBOOK
    title_en = "Operational Runbook"
    title_ar = "دليل التشغيل"
