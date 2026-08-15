from documentation.doc_models import DocumentType
from documentation.generators.wireless_design_generator import WirelessDesignGenerator
from ._documentation_helpers import resolved

def test_wireless_design_generator_generates_structured_content():
    result = WirelessDesignGenerator().generate(resolved(DocumentType.WIRELESS_DESIGN))
    assert result["document_type"] == DocumentType.WIRELESS_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
