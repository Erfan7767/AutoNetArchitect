"""Generator for the Assumption Register artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class AssumptionRegisterGenerator(BaseDocumentGenerator):
    """Generate Assumption Register from resolved source artifacts."""

    document_type = DocumentType.ASSUMPTION_REGISTER
    title_en = "Assumption Register"
    title_ar = "سجل الافتراضات"
