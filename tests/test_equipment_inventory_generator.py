from documentation.doc_models import DocumentType
from documentation.generators.equipment_inventory_generator import EquipmentInventoryGenerator
from ._documentation_helpers import resolved

def test_equipment_inventory_generator_generates_structured_content():
    result = EquipmentInventoryGenerator().generate(resolved(DocumentType.EQUIPMENT_INVENTORY))
    assert result["document_type"] == DocumentType.EQUIPMENT_INVENTORY.value
    assert result["sections"]
    assert "sot_basis" in result
