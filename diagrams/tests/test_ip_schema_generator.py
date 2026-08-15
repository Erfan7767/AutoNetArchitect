from diagrams.diagram_models import DiagramType
from diagrams.generators.ip_schema_generator import IPSchemaGenerator
from ._helpers import artifacts

def test_ip_schema_generator_is_source_driven():
    result = IPSchemaGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.IP_SCHEMA
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
