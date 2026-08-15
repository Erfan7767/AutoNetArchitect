from diagrams.diagram_models import DiagramType
from diagrams.generators.routing_domain_generator import RoutingDomainGenerator
from ._helpers import artifacts

def test_routing_domain_generator_is_source_driven():
    result = RoutingDomainGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.ROUTING_DOMAIN
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
