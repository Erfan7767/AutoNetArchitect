from diagrams.diagram_models import DiagramEdge, DiagramModel, DiagramNode, DiagramType, EdgeType, NodeType

def test_models_reject_dangling_edges():
    node = DiagramNode(node_id="a", node_type=NodeType.ROUTER, label="a")
    try:
        DiagramModel(diagram_type=DiagramType.LOGICAL_TOPOLOGY, title="x", nodes=[node], edges=[DiagramEdge(edge_id="e", source_node="a", target_node="missing", edge_type=EdgeType.LOGICAL)])
    except ValueError:
        return
    raise AssertionError("dangling edge was accepted")
