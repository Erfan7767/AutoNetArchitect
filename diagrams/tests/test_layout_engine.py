from diagrams.diagram_models import DiagramModel, DiagramNode, DiagramType, NodeType
from diagrams.layout_engine import LayoutEngine

def test_layout_engine_positions_and_scales_nodes():
    model = DiagramModel(diagram_type=DiagramType.LOGICAL_TOPOLOGY, title="x", nodes=[DiagramNode(node_id=str(i), node_type=NodeType.ROUTER, label=str(i)) for i in range(6)])
    result = LayoutEngine().layout(model)
    assert len({(node.position.x, node.position.y) for node in result.nodes}) == 6 and result.width >= 800
