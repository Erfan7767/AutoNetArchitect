from documentation.doc_models import DocumentType
from documentation.generators.change_procedure_generator import ChangeProcedureGenerator
from ._documentation_helpers import resolved

def test_change_procedure_generator_generates_structured_content():
    result = ChangeProcedureGenerator().generate(resolved(DocumentType.CHANGE_PROCEDURE))
    assert result["document_type"] == DocumentType.CHANGE_PROCEDURE.value
    assert result["sections"]
    assert "sot_basis" in result
