from diagrams.diagram_models import DiagramType
from diagrams.generators.dependency_graph_generator import DependencyGraphGenerator
from ._helpers import artifacts

def test_dependency_graph_generator_is_source_driven():
    result = DependencyGraphGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.DEPENDENCY_GRAPH
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
