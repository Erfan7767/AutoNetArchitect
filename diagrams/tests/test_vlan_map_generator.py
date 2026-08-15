from diagrams.diagram_models import DiagramType
from diagrams.generators.vlan_map_generator import VLANMapGenerator
from ._helpers import artifacts

def test_vlan_map_generator_is_source_driven():
    result = VLANMapGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.VLAN_MAP
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
