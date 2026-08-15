"""Performance test for evidence-bounded report generation."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import time

from documentation.doc_models import DocumentRequest, DocumentType, Language, OutputFormat, RedactionLevel
from documentation.doc_orchestrator import DocumentOrchestrator
from tests.final_test_helpers import fixture_project


def test_hld_json_report_generation_speed_and_redaction():
    with TemporaryDirectory() as tmp:
        project = fixture_project("enterprise_greenfield")
        request = DocumentRequest(document_type=DocumentType.DECISION_LOG, project_id=project["project_id"], output_format=OutputFormat.JSON, language=Language.ENGLISH, redaction_level=RedactionLevel.STANDARD, output_path=str(Path(tmp) / "decision-log.json"), minimum_completeness=0.0, allow_pending=False)
        started = time.perf_counter()
        document = DocumentOrchestrator().generate(request, {"project": project, "project_id": project["project_id"], "project_metadata": {"name": project["name"], "scope": "network architecture evidence test", "schema_version": "1.0"}, "decisions": [{"decision_id": "DEC-001", "decision": "segmented-campus", "rationale": "fixture-evidence"}], "sot_basis": {"status": "fixture"}, "evidence_basis": ["EVID-DESIGN-001"]})
        elapsed = time.perf_counter() - started
        assert elapsed < 15.0
        assert document.file_path.endswith("decision-log.json")
        assert Path(document.file_path).exists()
        assert document.redacted is True
