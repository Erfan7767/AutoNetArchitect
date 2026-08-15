from documentation.doc_models import DocumentType
from documentation.generators.atp_generator import ATPGenerator
from ._documentation_helpers import resolved

def test_atp_generator_generates_structured_content():
    result = ATPGenerator().generate(resolved(DocumentType.ATP))
    assert result["document_type"] == DocumentType.ATP.value
    assert result["sections"]
    assert "sot_basis" in result
