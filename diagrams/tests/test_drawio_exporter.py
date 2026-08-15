import tempfile
from pathlib import Path
from diagrams.exporters.drawio_exporter import DrawioExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_drawio_exporter_writes_editable_text():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.drawio"
        DrawioExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert path.exists() and path.stat().st_size > 0
        assert path.read_text(encoding="utf-8")
