"""Generator for the NAT Translation Documentation artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class NATDocumentationGenerator(BaseDocumentGenerator):
    """Generate NAT Translation Documentation from resolved source artifacts."""

    document_type = DocumentType.NAT_DOCUMENTATION
    title_en = "NAT Translation Documentation"
    title_ar = "توثيق ترجمة NAT"
