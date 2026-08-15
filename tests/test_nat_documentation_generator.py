from documentation.doc_models import DocumentType
from documentation.generators.nat_documentation_generator import NATDocumentationGenerator
from ._documentation_helpers import resolved

def test_nat_documentation_generator_generates_structured_content():
    result = NATDocumentationGenerator().generate(resolved(DocumentType.NAT_DOCUMENTATION))
    assert result["document_type"] == DocumentType.NAT_DOCUMENTATION.value
    assert result["sections"]
    assert "sot_basis" in result
