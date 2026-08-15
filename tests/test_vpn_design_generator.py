from documentation.doc_models import DocumentType
from documentation.generators.vpn_design_generator import VPNDesignGenerator
from ._documentation_helpers import resolved

def test_vpn_design_generator_generates_structured_content():
    result = VPNDesignGenerator().generate(resolved(DocumentType.VPN_DESIGN))
    assert result["document_type"] == DocumentType.VPN_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
