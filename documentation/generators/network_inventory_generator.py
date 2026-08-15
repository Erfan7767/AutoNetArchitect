"""Generator for the Network Device Inventory artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class NetworkInventoryGenerator(BaseDocumentGenerator):
    """Generate Network Device Inventory from resolved source artifacts."""

    document_type = DocumentType.NETWORK_INVENTORY
    title_en = "Network Device Inventory"
    title_ar = "جرد أجهزة الشبكة"
