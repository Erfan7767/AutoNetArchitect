import tempfile
from pathlib import Path
from documentation.renderers.json_renderer import JSONRenderer

def test_json_renderer_writes_machine_readable_output():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "doc.json"
        JSONRenderer().render({"title_en": "Test", "sections": []}, str(path))
        assert '"title_en": "Test"' in path.read_text(encoding="utf-8")
