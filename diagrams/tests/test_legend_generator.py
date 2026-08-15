from diagrams.diagram_models import DiagramModel, DiagramNode, DiagramType, NodeType
from diagrams.legend_generator import LegendGenerator

def test_legend_generator_reports_present_categories():
    model = DiagramModel(diagram_type=DiagramType.LOGICAL_TOPOLOGY, title="x", nodes=[DiagramNode(node_id="a", node_type=NodeType.ROUTER, label="a")])
    assert any(entry.category == "icon" and entry.label == "router" for entry in LegendGenerator().generate(model))
