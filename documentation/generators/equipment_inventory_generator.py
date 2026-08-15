"""Generator for the Equipment Inventory artifact."""
from __future__ import annotations

from ..doc_models import DocumentType
from .base_generator import BaseDocumentGenerator


class EquipmentInventoryGenerator(BaseDocumentGenerator):
    """Generate Equipment Inventory from resolved source artifacts."""

    document_type = DocumentType.EQUIPMENT_INVENTORY
    title_en = "Equipment Inventory"
    title_ar = "جرد المعدات"
