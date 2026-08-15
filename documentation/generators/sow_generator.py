"""Generator for the Statement of Work artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class SOWGenerator(BaseDocumentGenerator):
    """Generate Statement of Work from resolved source artifacts."""

    document_type = DocumentType.SOW
    title_en = "Statement of Work"
    title_ar = "بيان نطاق العمل"
