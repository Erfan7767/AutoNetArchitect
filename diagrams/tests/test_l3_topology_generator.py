from diagrams.diagram_models import DiagramType
from diagrams.generators.l3_topology_generator import L3TopologyGenerator
from ._helpers import artifacts

def test_l3_topology_generator_is_source_driven():
    result = L3TopologyGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.L3_TOPOLOGY
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
