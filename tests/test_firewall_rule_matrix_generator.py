from documentation.doc_models import DocumentType
from documentation.generators.firewall_rule_matrix_generator import FirewallRuleMatrixGenerator
from ._documentation_helpers import resolved

def test_firewall_rule_matrix_generator_generates_structured_content():
    result = FirewallRuleMatrixGenerator().generate(resolved(DocumentType.FIREWALL_RULE_MATRIX))
    assert result["document_type"] == DocumentType.FIREWALL_RULE_MATRIX.value
    assert result["sections"]
    assert "sot_basis" in result
