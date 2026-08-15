"""Floor plan diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType, NodeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class FloorPlanGenerator(BaseDiagramGenerator):
    """Generate floors, rooms, and equipment from explicit physical artifacts."""

    diagram_type = DiagramType.FLOOR_PLAN
    title = "Floor Plan Diagram"
    source_keys = ("floors", "rooms", "equipment", "devices", "nodes")
    default_edge_type = EdgeType.PHYSICAL

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build physical placement nodes without estimating dimensions."""
        result: dict[str, DiagramNode] = {}
        for index, record in enumerate(source_records(artifacts, ("floors", "rooms", "equipment", "devices", "nodes"))):
            node = self.node_from_record(record, index=index)
            if node is not None and self.in_scope(node, scope, scope_value):
                result[node.node_id] = node
        return list(result.values())

    def build_warnings(self, *, artifacts, nodes, edges):
        """Expose missing floor dimensions or location evidence."""
        warnings = super().build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        physical = artifacts.get("physical_design")
        if not isinstance(physical, Mapping) or not physical.get("site_dimensions"):
            warnings.append("PENDING: floor dimensions were not supplied; no scale is asserted")
        return warnings
