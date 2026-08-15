"""VLAN map diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramEdge, DiagramGroup, DiagramNode, DiagramType, EdgeType, GroupType, NodeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class VLANMapGenerator(BaseDiagramGenerator):
    """Generate VLAN and switch relationships from explicit VLAN records."""

    diagram_type = DiagramType.VLAN_MAP
    title = "VLAN Map Diagram"
    source_keys = ("vlans", "vlan_design", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.TRUNK

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build VLAN semantic nodes and supplied device nodes."""
        result: dict[str, DiagramNode] = {}
        for index, record in enumerate(source_records(artifacts, ("devices", "equipment", "nodes"))):
            node = self.node_from_record(record, index=index)
            if node is not None:
                result[node.node_id] = node
        for index, record in enumerate(source_records(artifacts, ("vlans", "vlan_design")), start=len(result)):
            vlan_id = text(record, "vlan_id", "id", "vlan", "name")
            if not vlan_id:
                continue
            semantic = {"id": f"vlan_{vlan_id}", "name": text(record, "name", "vlan_name") or f"VLAN {vlan_id}", "node_type": "vlan", "vlan": vlan_id, "subnet": record.get("subnet", ""), "status": record.get("status", "") }
            node = self.node_from_record(semantic, index=index)
            if node is not None:
                result[node.node_id] = node
        return list(result.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Link VLAN nodes to explicitly listed devices only."""
        node_ids = {node.node_id for node in nodes}
        edges: list[DiagramEdge] = []
        for index, record in enumerate(source_records(artifacts, ("vlans", "vlan_design"))):
            vlan_id = text(record, "vlan_id", "id", "vlan", "name")
            vlan_node = f"vlan_{vlan_id}" if vlan_id else ""
            devices = record.get("devices", record.get("device_ids", []))
            if not isinstance(devices, list) or vlan_node not in node_ids:
                continue
            for offset, device in enumerate(devices):
                target = str(device)
                if target not in node_ids:
                    continue
                edges.append(self.edge_from_record({"edge_id": f"vlan_edge_{index}_{offset}", "edge_type": "trunk", "label": f"VLAN {vlan_id}", "vlan": vlan_id, "status": record.get("status", "")}, source=vlan_node, target=target, index=index * 100 + offset))
        edges.extend(super().build_edges(artifacts=artifacts, nodes=nodes, detail_level=detail_level))
        return edges
