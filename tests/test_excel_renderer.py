import tempfile
from pathlib import Path
from documentation.renderers.excel_renderer import ExcelRenderer

def test_excel_renderer_renderer_writes_file():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "doc.xlsx"
        pages = ExcelRenderer().render({"title_en": "Test", "title_ar": "اختبار", "generated_at": "2026-08-14", "sections": [{"section_id": "s", "title_en": "Summary", "title_ar": "ملخص", "level": 1, "status": "complete", "content": [{"key": "value"}]}]}, str(path))
        assert path.exists() and path.stat().st_size > 0 and pages >= 1
