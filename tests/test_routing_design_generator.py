from documentation.doc_models import DocumentType
from documentation.generators.routing_design_generator import RoutingDesignGenerator
from ._documentation_helpers import resolved

def test_routing_design_generator_generates_structured_content():
    result = RoutingDesignGenerator().generate(resolved(DocumentType.ROUTING_DESIGN))
    assert result["document_type"] == DocumentType.ROUTING_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
