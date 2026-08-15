from diagrams.diagram_models import DiagramType
from diagrams.generators.vpn_topology_generator import VPNTopologyGenerator
from ._helpers import artifacts

def test_vpn_topology_generator_is_source_driven():
    result = VPNTopologyGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.VPN_TOPOLOGY
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
