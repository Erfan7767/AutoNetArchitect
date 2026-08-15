from documentation.doc_models import DocumentType
from documentation.generators.risk_register_generator import RiskRegisterGenerator
from ._documentation_helpers import resolved

def test_risk_register_generator_generates_structured_content():
    result = RiskRegisterGenerator().generate(resolved(DocumentType.RISK_REGISTER))
    assert result["document_type"] == DocumentType.RISK_REGISTER.value
    assert result["sections"]
    assert "sot_basis" in result
