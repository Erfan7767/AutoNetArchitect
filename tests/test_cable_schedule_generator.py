from documentation.doc_models import DocumentType
from documentation.generators.cable_schedule_generator import CableScheduleGenerator
from ._documentation_helpers import resolved

def test_cable_schedule_generator_generates_structured_content():
    result = CableScheduleGenerator().generate(resolved(DocumentType.CABLE_SCHEDULE))
    assert result["document_type"] == DocumentType.CABLE_SCHEDULE.value
    assert result["sections"]
    assert "sot_basis" in result
