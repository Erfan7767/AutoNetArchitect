from documentation.doc_models import DocumentType
from documentation.generators.operational_runbook_generator import OperationalRunbookGenerator
from ._documentation_helpers import resolved

def test_operational_runbook_generator_generates_structured_content():
    result = OperationalRunbookGenerator().generate(resolved(DocumentType.OPERATIONAL_RUNBOOK))
    assert result["document_type"] == DocumentType.OPERATIONAL_RUNBOOK.value
    assert result["sections"]
    assert "sot_basis" in result
