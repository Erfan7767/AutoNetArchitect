import tempfile
from pathlib import Path
from documentation.renderers.html_renderer import HTMLRenderer

def test_html_renderer_writes_bilingual_html():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "doc.html"
        HTMLRenderer().render({"title_en": "Test", "title_ar": "اختبار", "sections": []}, str(path))
        assert "اختبار" in path.read_text(encoding="utf-8")
