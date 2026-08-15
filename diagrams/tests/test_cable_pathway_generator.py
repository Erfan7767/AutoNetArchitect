from diagrams.diagram_models import DiagramType
from diagrams.generators.cable_pathway_generator import CablePathwayGenerator
from ._helpers import artifacts

def test_cable_pathway_generator_is_source_driven():
    result = CablePathwayGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.CABLE_PATHWAY
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
