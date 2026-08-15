"""Generator for the ACL Documentation artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class ACLDocumentationGenerator(BaseDocumentGenerator):
    """Generate ACL Documentation from resolved source artifacts."""

    document_type = DocumentType.ACL_DOCUMENTATION
    title_en = "ACL Documentation"
    title_ar = "توثيق قوائم التحكم"
