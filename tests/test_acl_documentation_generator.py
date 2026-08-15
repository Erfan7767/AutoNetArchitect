from documentation.doc_models import DocumentType
from documentation.generators.acl_documentation_generator import ACLDocumentationGenerator
from ._documentation_helpers import resolved

def test_acl_documentation_generator_generates_structured_content():
    result = ACLDocumentationGenerator().generate(resolved(DocumentType.ACL_DOCUMENTATION))
    assert result["document_type"] == DocumentType.ACL_DOCUMENTATION.value
    assert result["sections"]
    assert "sot_basis" in result
