from diagrams.diagram_models import DiagramType
from diagrams.generators.site_overview_generator import SiteOverviewGenerator
from ._helpers import artifacts

def test_site_overview_generator_is_source_driven():
    result = SiteOverviewGenerator().generate(artifacts=artifacts(), detail_level="detailed")
    assert result.diagram_type == DiagramType.SITE_OVERVIEW
    assert all(edge.source_node in {node.node_id for node in result.nodes} and edge.target_node in {node.node_id for node in result.nodes} for edge in result.edges)
