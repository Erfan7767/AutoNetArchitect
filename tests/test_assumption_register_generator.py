from documentation.doc_models import DocumentType
from documentation.generators.assumption_register_generator import AssumptionRegisterGenerator
from ._documentation_helpers import resolved

def test_assumption_register_generator_generates_structured_content():
    result = AssumptionRegisterGenerator().generate(resolved(DocumentType.ASSUMPTION_REGISTER))
    assert result["document_type"] == DocumentType.ASSUMPTION_REGISTER.value
    assert result["sections"]
    assert "sot_basis" in result
