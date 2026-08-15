from documentation.doc_models import DocumentType
from documentation.generators.dr_plan_generator import DRPlanGenerator
from ._documentation_helpers import resolved

def test_dr_plan_generator_generates_structured_content():
    result = DRPlanGenerator().generate(resolved(DocumentType.DR_PLAN))
    assert result["document_type"] == DocumentType.DR_PLAN.value
    assert result["sections"]
    assert "sot_basis" in result
