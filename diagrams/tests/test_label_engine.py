from diagrams.diagram_models import DiagramNode, DiagramModel, DiagramType, LabelConfig, NodeType
from diagrams.label_engine import LabelEngine

def test_label_engine_marks_unconfirmed_nodes():
    model = DiagramModel(diagram_type=DiagramType.LOGICAL_TOPOLOGY, title="x", nodes=[DiagramNode(node_id="a", node_type=NodeType.ROUTER, label="a", uncertain=True, metadata={"hostname": "r1"})])
    result = LabelEngine().apply_labels(model, LabelConfig())
    assert result.nodes[0].label.startswith("UNCONFIRMED:")
