"""Generator for the Disaster Recovery Plan artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class DRPlanGenerator(BaseDocumentGenerator):
    """Generate Disaster Recovery Plan from resolved source artifacts."""

    document_type = DocumentType.DR_PLAN
    title_en = "Disaster Recovery Plan"
    title_ar = "خطة التعافي من الكوارث"
