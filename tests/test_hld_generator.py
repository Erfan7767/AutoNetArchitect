from documentation.doc_models import DocumentType
from documentation.generators.hld_generator import HLDGenerator
from ._documentation_helpers import resolved

def test_hld_generator_generates_structured_content():
    result = HLDGenerator().generate(resolved(DocumentType.HLD))
    assert result["document_type"] == DocumentType.HLD.value
    assert result["sections"]
    assert "sot_basis" in result
