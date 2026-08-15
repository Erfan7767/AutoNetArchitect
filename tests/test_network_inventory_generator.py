from documentation.doc_models import DocumentType
from documentation.generators.network_inventory_generator import NetworkInventoryGenerator
from ._documentation_helpers import resolved

def test_network_inventory_generator_generates_structured_content():
    result = NetworkInventoryGenerator().generate(resolved(DocumentType.NETWORK_INVENTORY))
    assert result["document_type"] == DocumentType.NETWORK_INVENTORY.value
    assert result["sections"]
    assert "sot_basis" in result
