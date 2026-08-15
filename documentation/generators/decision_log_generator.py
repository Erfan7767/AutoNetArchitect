"""Generator for the Design Decision Log artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class DecisionLogGenerator(BaseDocumentGenerator):
    """Generate Design Decision Log from resolved source artifacts."""

    document_type = DocumentType.DECISION_LOG
    title_en = "Design Decision Log"
    title_ar = "سجل قرارات التصميم"
