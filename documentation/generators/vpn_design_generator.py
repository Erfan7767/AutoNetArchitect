"""Generator for the VPN Design Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class VPNDesignGenerator(BaseDocumentGenerator):
    """Generate VPN Design Document from resolved source artifacts."""

    document_type = DocumentType.VPN_DESIGN
    title_en = "VPN Design Document"
    title_ar = "وثيقة تصميم VPN"
