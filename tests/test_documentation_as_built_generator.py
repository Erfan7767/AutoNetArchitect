from documentation.doc_models import DocumentType
from documentation.generators.as_built_generator import AsBuiltGenerator
from tests._documentation_helpers import resolved


def test_documentation_as_built_generator_generates_actual_state_sections():
    result = AsBuiltGenerator().generate(resolved(DocumentType.AS_BUILT))
    assert result["document_type"] == "as_built"
    assert any(item["section_id"] == "actual_state" for item in result["sections"])
