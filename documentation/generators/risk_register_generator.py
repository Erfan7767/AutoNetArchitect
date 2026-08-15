"""Generator for the Risk Register artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class RiskRegisterGenerator(BaseDocumentGenerator):
    """Generate Risk Register from resolved source artifacts."""

    document_type = DocumentType.RISK_REGISTER
    title_en = "Risk Register"
    title_ar = "سجل المخاطر"
