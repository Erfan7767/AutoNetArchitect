from documentation.doc_models import DocumentType
from documentation.generators.physical_layout_generator import PhysicalLayoutGenerator
from ._documentation_helpers import resolved

def test_physical_layout_generator_generates_structured_content():
    result = PhysicalLayoutGenerator().generate(resolved(DocumentType.PHYSICAL_LAYOUT))
    assert result["document_type"] == DocumentType.PHYSICAL_LAYOUT.value
    assert result["sections"]
    assert "sot_basis" in result
