from documentation.doc_models import DocumentType
from documentation.generators.decision_log_generator import DecisionLogGenerator
from ._documentation_helpers import resolved

def test_decision_log_generator_generates_structured_content():
    result = DecisionLogGenerator().generate(resolved(DocumentType.DECISION_LOG))
    assert result["document_type"] == DocumentType.DECISION_LOG.value
    assert result["sections"]
    assert "sot_basis" in result
