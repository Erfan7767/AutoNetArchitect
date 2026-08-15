import tempfile
from pathlib import Path
from diagrams.exporters.graphviz_exporter import GraphvizExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_graphviz_exporter_writes_editable_text():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.dot"
        GraphvizExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert path.exists() and path.stat().st_size > 0
        assert path.read_text(encoding="utf-8")
