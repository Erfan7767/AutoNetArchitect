from documentation.doc_models import ContentType, DocumentSection, DocumentType
from documentation.doc_section_registry import DocumentSectionRegistry

def test_registry_customization_and_not_applicable():
    registry = DocumentSectionRegistry()
    registry.add_custom(DocumentType.HLD, DocumentSection(section_id="custom", section_title_en="Custom", section_title_ar="مخصص", section_level=2, content_type=ContentType.TEXT, data_source="custom", mandatory=False))
    registry.mark_not_applicable(DocumentType.HLD, "custom", "not in project scope")
    assert any(item.section_id == "custom" and item.status.value == "not_applicable" for item in registry.get(DocumentType.HLD))
