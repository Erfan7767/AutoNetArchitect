from documentation.doc_models import DocumentType
from documentation.generators.vlan_database_generator import VLANDatabaseGenerator
from ._documentation_helpers import resolved

def test_vlan_database_generator_generates_structured_content():
    result = VLANDatabaseGenerator().generate(resolved(DocumentType.VLAN_DATABASE))
    assert result["document_type"] == DocumentType.VLAN_DATABASE.value
    assert result["sections"]
    assert "sot_basis" in result
