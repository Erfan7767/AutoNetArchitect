from documentation.doc_models import DocumentType
from documentation.generators.lld_generator import LLDGenerator
from ._documentation_helpers import resolved

def test_lld_generator_generates_structured_content():
    result = LLDGenerator().generate(resolved(DocumentType.LLD))
    assert result["document_type"] == DocumentType.LLD.value
    assert result["sections"]
    assert "sot_basis" in result
