from documentation.doc_models import DocumentType
from documentation.generators.compliance_report_generator import ComplianceReportGenerator
from ._documentation_helpers import resolved

def test_compliance_report_generator_generates_structured_content():
    result = ComplianceReportGenerator().generate(resolved(DocumentType.COMPLIANCE_REPORT))
    assert result["document_type"] == DocumentType.COMPLIANCE_REPORT.value
    assert result["sections"]
    assert "sot_basis" in result
