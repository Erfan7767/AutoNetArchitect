"""Cable pathway diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramEdge, DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class CablePathwayGenerator(BaseDiagramGenerator):
    """Generate cable endpoints and pathway links from complete mapping records."""

    diagram_type = DiagramType.CABLE_PATHWAY
    title = "Cable Pathway Diagram"
    source_keys = ("pathways", "cable_runs", "cables", "mappings", "nodes", "equipment")
    default_edge_type = EdgeType.PHYSICAL

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Create endpoint nodes from both ends of explicit cable records."""
        result: dict[str, DiagramNode] = {}
        rows = source_records(artifacts, self.source_keys)
        for index, record in enumerate(rows):
            for key in ("source_node", "source", "device", "from_device", "local_device", "target_node", "target", "remote_device", "to_device", "peer_device"):
                value = text(record, key)
                if value and value not in result:
                    endpoint = {"id": value, "hostname": value, "node_type": "unknown", "status": record.get("status", "") , "site": record.get("site", ""), "building": record.get("building", ""), "floor": record.get("floor", "")}
                    node = self.node_from_record(endpoint, index=index)
                    if node is not None:
                        result[value] = node
        return list(result.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Use cable IDs, media, pathway, and interface labels only when supplied."""
        return super().build_edges(artifacts=artifacts, nodes=nodes, detail_level=detail_level)
