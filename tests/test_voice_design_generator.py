from documentation.doc_models import DocumentType
from documentation.generators.voice_design_generator import VoiceDesignGenerator
from ._documentation_helpers import resolved

def test_voice_design_generator_generates_structured_content():
    result = VoiceDesignGenerator().generate(resolved(DocumentType.VOICE_DESIGN))
    assert result["document_type"] == DocumentType.VOICE_DESIGN.value
    assert result["sections"]
    assert "sot_basis" in result
