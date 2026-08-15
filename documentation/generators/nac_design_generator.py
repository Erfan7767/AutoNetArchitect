"""Generator for the NAC and 802.1X Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class NACDesignGenerator(BaseDocumentGenerator):
    """Generate NAC and 802.1X Design Document from resolved source artifacts."""

    document_type = DocumentType.NAC_DESIGN
    title_en = "NAC and 802.1X Design Document"
    title_ar = "وثيقة تصميم NAC و802.1X"
