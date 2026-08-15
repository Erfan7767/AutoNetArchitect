from documentation.doc_models import DocumentType
from documentation.generators.capacity_report_generator import CapacityReportGenerator
from ._documentation_helpers import resolved

def test_capacity_report_generator_generates_structured_content():
    result = CapacityReportGenerator().generate(resolved(DocumentType.CAPACITY_REPORT))
    assert result["document_type"] == DocumentType.CAPACITY_REPORT.value
    assert result["sections"]
    assert "sot_basis" in result
