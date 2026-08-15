import tempfile
from pathlib import Path
from diagrams import DiagramOrchestrator, DiagramRequest, DiagramType, OutputFormat
from ._helpers import artifacts

def test_orchestrator_generates_svg_with_traceability():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "logical.svg"
        result = DiagramOrchestrator().generate(DiagramRequest(diagram_type=DiagramType.LOGICAL_TOPOLOGY, project_id="p-1", output_format=OutputFormat.SVG, output_path=str(path), sot_basis={"DESIGN": "sot:design:p-1"}), artifacts())
        assert path.exists() and result.node_count == 3 and result.edge_count == 2
        assert result.sot_basis["DESIGN"] == "sot:design:p-1"
