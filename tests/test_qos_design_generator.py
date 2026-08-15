from documentation.doc_models import DocumentType
from documentation.generators.qos_design_generator import QoSDesignGenerator
from ._documentation_helpers import resolved

def test_qos_design_generator_generates_structured_content():
    result = QoSDesignGenerator().generate(resolved(DocumentType.QOS_DESIGN))
    assert result["document_type"] == DocumentType.QOS_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
