from documentation.doc_models import DocumentType
from documentation.generators.sow_generator import SOWGenerator
from ._documentation_helpers import resolved

def test_sow_generator_generates_structured_content():
    result = SOWGenerator().generate(resolved(DocumentType.SOW))
    assert result["document_type"] == DocumentType.SOW.value
    assert result["sections"]
    assert "sot_basis" in result
