from documentation.doc_models import DocumentType
from documentation.generators.troubleshooting_guide_generator import TroubleshootingGuideGenerator
from ._documentation_helpers import resolved

def test_troubleshooting_guide_generator_generates_structured_content():
    result = TroubleshootingGuideGenerator().generate(resolved(DocumentType.TROUBLESHOOTING_GUIDE))
    assert result["document_type"] == DocumentType.TROUBLESHOOTING_GUIDE.value
    assert result["sections"]
    assert "sot_basis" in result
