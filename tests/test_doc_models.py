from documentation.doc_models import DocumentType, DocumentRequest, OutputFormat, Language

def test_document_type_catalog_and_request_contract():
    request = DocumentRequest(document_type=DocumentType.HLD, project_id="p-1", output_format=OutputFormat.JSON, output_path="/tmp/hld.json", language=Language.BILINGUAL)
    assert request.document_type == DocumentType.HLD
    assert len(DocumentType) == 34
