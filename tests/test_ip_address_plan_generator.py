from documentation.doc_models import DocumentType
from documentation.generators.ip_address_plan_generator import IPAddressPlanGenerator
from ._documentation_helpers import resolved

def test_ip_address_plan_generator_generates_structured_content():
    result = IPAddressPlanGenerator().generate(resolved(DocumentType.IP_ADDRESS_PLAN))
    assert result["document_type"] == DocumentType.IP_ADDRESS_PLAN.value
    assert result["sections"]
    assert "sot_basis" in result
