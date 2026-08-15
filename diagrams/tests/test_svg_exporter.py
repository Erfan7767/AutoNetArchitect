import tempfile
from pathlib import Path
from diagrams.exporters.svg_exporter import SVGExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_svg_exporter_writes_vector():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.svg"
        SVGExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert "<svg" in path.read_text(encoding="utf-8")
