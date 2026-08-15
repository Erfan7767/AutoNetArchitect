from documentation.doc_models import DocumentType
from documentation.generators.wan_design_generator import WANDesignGenerator
from ._documentation_helpers import resolved

def test_wan_design_generator_generates_structured_content():
    result = WANDesignGenerator().generate(resolved(DocumentType.WAN_DESIGN))
    assert result["document_type"] == DocumentType.WAN_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
