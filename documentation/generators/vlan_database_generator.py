"""Generator for the VLAN Database Document artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class VLANDatabaseGenerator(BaseDocumentGenerator):
    """Generate VLAN Database Document from resolved source artifacts."""

    document_type = DocumentType.VLAN_DATABASE
    title_en = "VLAN Database Document"
    title_ar = "وثيقة قاعدة بيانات VLAN"
