import tempfile
from pathlib import Path
from diagrams.exporters.mermaid_exporter import MermaidExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_mermaid_exporter_writes_editable_text():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.mmd"
        MermaidExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert path.exists() and path.stat().st_size > 0
        assert path.read_text(encoding="utf-8")
