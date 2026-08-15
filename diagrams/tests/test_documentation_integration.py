from diagrams import DiagramOrchestrator, DiagramRequest, DiagramType
from ._helpers import artifacts


def test_diagram_model_can_be_consumed_by_documentation_artifacts():
    engine = DiagramOrchestrator()
    model = engine.model(DiagramRequest(diagram_type=DiagramType.PHYSICAL_TOPOLOGY, project_id="p-1", output_path="/tmp/diagram.svg"), artifacts())
    artifact = engine.documentation_artifact(model)
    assert artifact["diagram_type"] == "physical_topology"
    assert artifact["nodes"] and "edges" in artifact and "legend" in artifact
