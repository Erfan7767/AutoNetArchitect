import tempfile
from pathlib import Path
from diagrams.exporters.pdf_exporter import PDFExporter
from ._helpers import model
from diagrams.diagram_models import DiagramType

def test_pdf_exporter_writes_pdf():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "diagram.pdf"
        PDFExporter().export(model(DiagramType.LOGICAL_TOPOLOGY), path)
        assert path.exists() and path.stat().st_size > 0
