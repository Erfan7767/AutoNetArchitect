import tempfile
from pathlib import Path
from documentation import DocumentOrchestrator
from documentation.doc_models import DocumentRequest, DocumentType, OutputFormat, Language, RedactionLevel
from ._documentation_helpers import artifacts

def test_orchestrator_generates_source_driven_json():
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "hld.json"
        artifact = DocumentOrchestrator().generate(DocumentRequest(document_type=DocumentType.HLD, project_id="p-1", output_format=OutputFormat.JSON, language=Language.BILINGUAL, redaction_level=RedactionLevel.STANDARD, output_path=str(output)), artifacts())
        assert output.exists() and artifact.sot_basis["DESIGN"] == "sot:design:p-1"
        assert artifact.redacted is True
