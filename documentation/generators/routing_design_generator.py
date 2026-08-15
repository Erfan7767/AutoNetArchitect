"""Generator for the Routing Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class RoutingDesignGenerator(BaseDocumentGenerator):
    """Generate Routing Design Document from resolved source artifacts."""

    document_type = DocumentType.ROUTING_DESIGN
    title_en = "Routing Design Document"
    title_ar = "وثيقة تصميم التوجيه"
