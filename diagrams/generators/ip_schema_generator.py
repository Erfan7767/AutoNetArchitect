"""Hierarchical IP schema diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramEdge, DiagramNode, DiagramType, EdgeType, NodeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class IPSchemaGenerator(BaseDiagramGenerator):
    """Generate supernet-to-allocation trees from explicit parent relationships."""

    diagram_type = DiagramType.IP_SCHEMA
    title = "IP Addressing Schema Diagram"
    source_keys = ("ip_allocations", "ip_design", "subnets", "sites", "vlans", "nodes")
    default_edge_type = EdgeType.LOGICAL

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build IP allocation nodes without fabricating hierarchy levels."""
        result: dict[str, DiagramNode] = {}
        for index, record in enumerate(source_records(artifacts, ("ip_allocations", "ip_design", "subnets", "sites", "vlans"))):
            cidr = text(record, "cidr", "network", "subnet", "prefix")
            if not cidr:
                continue
            identifier = text(record, "id", "allocation_id", "name") or cidr
            item = {"id": f"ip_{identifier}", "name": cidr, "label": cidr, "node_type": "subnet", "subnet": cidr, "site": record.get("site", ""), "status": record.get("status", ""), "confidence": record.get("confidence", 1.0)}
            node = self.node_from_record(item, index=index)
            if node is not None:
                result[node.node_id] = node
        return list(result.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Link allocations only where parent/child identifiers are supplied."""
        node_ids = {node.node_id for node in nodes}
        edges: list[DiagramEdge] = []
        for index, record in enumerate(source_records(artifacts, self.source_keys)):
            child = text(record, "id", "allocation_id", "name", "cidr", "network", "subnet")
            parent = text(record, "parent_id", "parent", "supernet_id", "site_id")
            if not child or not parent:
                continue
            child_id = child if child.startswith("ip_") else f"ip_{child}"
            parent_id = parent if parent.startswith("ip_") else f"ip_{parent}"
            if child_id not in node_ids or parent_id not in node_ids:
                continue
            edges.append(self.edge_from_record({"id": f"ip_edge_{index}", "edge_type": "logical", "label": "allocation"}, source=parent_id, target=child_id, index=index))
        return edges
