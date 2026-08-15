import tempfile
from pathlib import Path
from diagrams.exporters.png_exporter import PNGExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_png_exporter_writes_raster():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.png"
        PNGExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert path.exists() and path.stat().st_size > 0
