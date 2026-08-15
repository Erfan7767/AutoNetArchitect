"""Generator for the Port Mapping Matrix artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class PortMappingGenerator(BaseDocumentGenerator):
    """Generate Port Mapping Matrix from resolved source artifacts."""

    document_type = DocumentType.PORT_MAPPING
    title_en = "Port Mapping Matrix"
    title_ar = "مصفوفة توزيع المنافذ"
