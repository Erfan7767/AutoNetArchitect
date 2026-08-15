from documentation.doc_models import DocumentType
from documentation.doc_data_resolver import DocDataResolver
from documentation.doc_section_registry import DocumentSectionRegistry
from ._documentation_helpers import artifacts

def test_resolver_marks_missing_source_as_pending():
    data = artifacts()
    data.pop("security_design")
    resolved = DocDataResolver().resolve(document_type=DocumentType.SECURITY_DESIGN, artifacts=data, registry=DocumentSectionRegistry())
    assert "zones_and_controls" in resolved.pending_sections
    assert any(item.pending_reason and "PENDING:" in item.pending_reason for item in resolved.sections)
