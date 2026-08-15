"""Generator for the Firewall Rule Matrix artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class FirewallRuleMatrixGenerator(BaseDocumentGenerator):
    """Generate Firewall Rule Matrix from resolved source artifacts."""

    document_type = DocumentType.FIREWALL_RULE_MATRIX
    title_en = "Firewall Rule Matrix"
    title_ar = "مصفوفة قواعد الجدار الناري"
