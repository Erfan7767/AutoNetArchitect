from diagrams.diagram_models import DiagramType
from diagrams.generators.wan_topology_generator import WANTopologyGenerator
from ._helpers import artifacts

def test_wan_topology_generator_is_source_driven():
    result = WANTopologyGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.WAN_TOPOLOGY
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
