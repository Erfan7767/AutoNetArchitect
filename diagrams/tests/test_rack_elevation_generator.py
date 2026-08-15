from diagrams.diagram_models import DiagramType
from diagrams.generators.rack_elevation_generator import RackElevationGenerator
from ._helpers import artifacts

def test_rack_elevation_generator_is_source_driven():
    result = RackElevationGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.RACK_ELEVATION
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
