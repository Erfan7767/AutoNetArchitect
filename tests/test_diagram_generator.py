import tempfile
from pathlib import Path
from reports.diagram_generator import DiagramGenerator

def test_diagram_generator_writes_mermaid_with_basis_and_safe_ids():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "topology.mmd"
        artifact = DiagramGenerator().generate(title="Topology", nodes=[{"id":"core-1", "label":"Core"}, {"id":"edge-1", "label":"Edge"}], links=[{"source":"core-1", "target":"edge-1", "label":"10G"}], output_path=path, sot_basis={"DESIGN":"sot:design"}, evidence_basis=["ev-topology"])
        text = path.read_text(encoding="utf-8")
        assert "flowchart LR" in text and "core_1" in text and "sot:design" in text
        assert artifact.format == "mmd"
