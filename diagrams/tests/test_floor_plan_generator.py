from diagrams.diagram_models import DiagramType
from diagrams.generators.floor_plan_generator import FloorPlanGenerator
from ._helpers import artifacts

def test_floor_plan_generator_is_source_driven():
    result = FloorPlanGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.FLOOR_PLAN
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
