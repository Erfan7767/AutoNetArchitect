"""Service dependency graph generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramEdge, DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class DependencyGraphGenerator(BaseDiagramGenerator):
    """Generate service dependency nodes and explicit dependency edges."""

    diagram_type = DiagramType.DEPENDENCY_GRAPH
    title = "Service Dependency Graph"
    source_keys = ("dependencies", "services", "service_dependencies", "nodes")
    default_edge_type = EdgeType.DEPENDENCY

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope, scope_value, detail_level: str) -> list[DiagramNode]:
        """Build service nodes from service records and dependency endpoints."""
        result: dict[str, DiagramNode] = {}
        rows = source_records(artifacts, self.source_keys)
        for index, record in enumerate(rows):
            node = self.node_from_record({**record, "node_type": record.get("node_type", "service")}, index=index)
            if node is not None:
                result[node.node_id] = node
            for key in ("depends_on", "dependency", "dependencies"):
                dependencies = record.get(key, [])
                if isinstance(dependencies, list):
                    for dependency in dependencies:
                        name = str(dependency)
                        if name and name not in result:
                            dependency_node = self.node_from_record({"id": name, "name": name, "node_type": "service", "status": "unverified"}, index=index + len(result))
                            if dependency_node is not None:
                                result[name] = dependency_node
        return list(result.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Create one directed edge per explicitly declared dependency."""
        node_ids = {node.node_id for node in nodes}
        result: list[DiagramEdge] = []
        for index, record in enumerate(source_records(artifacts, self.source_keys)):
            source = text(record, "id", "service_id", "name", "node_id")
            dependencies = record.get("depends_on", record.get("dependency", record.get("dependencies", [])))
            if not source or not isinstance(dependencies, list) or source not in node_ids:
                continue
            for offset, dependency in enumerate(dependencies):
                target = str(dependency)
                if target in node_ids:
                    result.append(self.edge_from_record({"id": f"dependency_{index}_{offset}", "edge_type": "dependency", "label": "depends on"}, source=source, target=target, index=index * 100 + offset))
        return result
