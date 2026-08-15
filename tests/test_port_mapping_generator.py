from documentation.doc_models import DocumentType
from documentation.generators.port_mapping_generator import PortMappingGenerator
from ._documentation_helpers import resolved

def test_port_mapping_generator_generates_structured_content():
    result = PortMappingGenerator().generate(resolved(DocumentType.PORT_MAPPING))
    assert result["document_type"] == DocumentType.PORT_MAPPING.value
    assert result["sections"]
    assert "sot_basis" in result
