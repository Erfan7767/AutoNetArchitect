from documentation.doc_models import DocumentType
from documentation.generators.handover_pack_generator import HandoverPackGenerator
from tests._documentation_helpers import resolved


def test_documentation_handover_pack_generator_generates_index_and_actions():
    result = HandoverPackGenerator().generate(resolved(DocumentType.HANDOVER_PACK))
    assert result["document_type"] == "handover_pack"
    assert any(item["section_id"] == "document_index" for item in result["sections"])
