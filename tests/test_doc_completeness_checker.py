from documentation.doc_completeness_checker import DocCompletenessChecker
from documentation.doc_data_resolver import DocDataResolver
from documentation.doc_models import DocumentType
from documentation.doc_section_registry import DocumentSectionRegistry
from ._documentation_helpers import artifacts

def test_completeness_reports_blocking_mandatory_sections():
    data = artifacts(); data.pop("bom")
    resolved = DocDataResolver().resolve(document_type=DocumentType.BOM, artifacts=data, registry=DocumentSectionRegistry())
    result = DocCompletenessChecker().check(resolved)
    assert result.can_render is False
    assert "bom_table" in result.pending_sections
