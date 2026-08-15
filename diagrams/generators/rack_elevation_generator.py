"""Rack elevation diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType, NodeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class RackElevationGenerator(BaseDiagramGenerator):
    """Generate rack and equipment nodes with supplied RU metadata."""

    diagram_type = DiagramType.RACK_ELEVATION
    title = "Rack Elevation Diagram"
    source_keys = ("racks", "equipment", "devices", "nodes")
    default_edge_type = EdgeType.PHYSICAL

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build rack containers and equipment records; absent RU fields stay uncertain."""
        result: dict[str, DiagramNode] = {}
        rows = source_records(artifacts, ("racks", "equipment", "devices", "nodes"))
        for index, record in enumerate(rows):
            if not text(record, "node_id", "id", "device_id", "hostname", "device", "name", "rack"):
                continue
            node = self.node_from_record(record, index=index)
            if node is not None:
                result[node.node_id] = node
        return list(result.values())

    def build_warnings(self, *, artifacts, nodes, edges):
        """Warn when rack placements are not supplied."""
        warnings = super().build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        if any("ru_position" not in node.metadata for node in nodes if node.node_type not in {NodeType.RACK}):
            warnings.append("UNCONFIRMED: RU position not supplied for one or more equipment records")
        return warnings
