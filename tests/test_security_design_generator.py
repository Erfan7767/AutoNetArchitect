from documentation.doc_models import DocumentType
from documentation.generators.security_design_generator import SecurityDesignGenerator
from ._documentation_helpers import resolved

def test_security_design_generator_generates_structured_content():
    result = SecurityDesignGenerator().generate(resolved(DocumentType.SECURITY_DESIGN))
    assert result["document_type"] == DocumentType.SECURITY_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
