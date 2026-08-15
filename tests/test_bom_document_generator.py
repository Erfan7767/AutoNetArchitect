from documentation.doc_models import DocumentType
from documentation.generators.bom_document_generator import BOMDocumentGenerator
from ._documentation_helpers import resolved

def test_bom_document_generator_generates_structured_content():
    result = BOMDocumentGenerator().generate(resolved(DocumentType.BOM))
    assert result["document_type"] == DocumentType.BOM.value
    assert result["sections"]
    assert "sot_basis" in result
