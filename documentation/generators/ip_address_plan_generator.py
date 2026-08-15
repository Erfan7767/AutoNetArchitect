"""Generator for the IP Address Management Sheet artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class IPAddressPlanGenerator(BaseDocumentGenerator):
    """Generate IP Address Management Sheet from resolved source artifacts."""

    document_type = DocumentType.IP_ADDRESS_PLAN
    title_en = "IP Address Management Sheet"
    title_ar = "ورقة إدارة عناوين IP"
