from documentation.doc_models import DocumentType
from documentation.generators.nac_design_generator import NACDesignGenerator
from ._documentation_helpers import resolved

def test_nac_design_generator_generates_structured_content():
    result = NACDesignGenerator().generate(resolved(DocumentType.NAC_DESIGN))
    assert result["document_type"] == DocumentType.NAC_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
