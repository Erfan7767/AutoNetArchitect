"""Site overview diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class SiteOverviewGenerator(BaseDiagramGenerator):
    """Generate sites and buildings from explicit site records."""

    diagram_type = DiagramType.SITE_OVERVIEW
    title = "Site Overview Diagram"
    source_keys = ("sites", "buildings", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.LOGICAL

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Create site/building/device nodes from supplied records."""
        result: dict[str, DiagramNode] = {}
        for index, record in enumerate(source_records(artifacts, ("sites", "buildings", "devices", "equipment", "nodes"))):
            node = self.node_from_record(record, index=index)
            if node is not None and self.in_scope(node, scope, scope_value):
                result[node.node_id] = node
        return list(result.values())
