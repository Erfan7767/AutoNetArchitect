"""Generator for the Standard Change Procedures artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class ChangeProcedureGenerator(BaseDocumentGenerator):
    """Generate Standard Change Procedures from resolved source artifacts."""

    document_type = DocumentType.CHANGE_PROCEDURE
    title_en = "Standard Change Procedures"
    title_ar = "إجراءات التغيير القياسية"
