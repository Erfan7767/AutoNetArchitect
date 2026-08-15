"""Routing domain diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramEdge, DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class RoutingDomainGenerator(BaseDiagramGenerator):
    """Generate routing areas, AS domains, and explicit adjacencies."""

    diagram_type = DiagramType.ROUTING_DOMAIN
    title = "Routing Domain Diagram"
    source_keys = ("routing_domains", "routing_design", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.ROUTING

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build domain and device nodes from routing records."""
        result: dict[str, DiagramNode] = {}
        for index, record in enumerate(source_records(artifacts, ("devices", "equipment", "nodes"))):
            node = self.node_from_record(record, index=index)
            if node is not None:
                result[node.node_id] = node
        for index, record in enumerate(source_records(artifacts, ("routing_domains", "routing_design")), start=len(result)):
            domain = text(record, "domain_id", "area_id", "area", "asn", "as_number", "protocol")
            if not domain:
                continue
            item = {"id": f"route_{domain}", "name": text(record, "label", "name", "protocol") or domain, "node_type": "service", "role": "routing_domain", "area": domain, "status": record.get("status", "") }
            node = self.node_from_record(item, index=index)
            if node is not None:
                result[node.node_id] = node
        return list(result.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Use explicit neighbor/adjacency pairs and never infer a full mesh."""
        return super().build_edges(artifacts=artifacts, nodes=nodes, detail_level=detail_level)
