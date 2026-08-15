from diagrams.diagram_models import DiagramType
from diagrams.generators.dr_topology_generator import DRTopologyGenerator
from ._helpers import artifacts

def test_dr_topology_generator_is_source_driven():
    result = DRTopologyGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.DR_TOPOLOGY
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
