"""Deterministic, bounded layout algorithms for network diagrams."""
from __future__ import annotations

import math
from typing import Iterable

from .diagram_models import DiagramModel, DiagramNode, DiagramType, Position


class LayoutEngine:
    """Position diagram nodes using readable deterministic layouts."""

    def layout(self, model: DiagramModel, *, algorithm: str | None = None, minimum_distance: float = 150.0) -> DiagramModel:
        """Return a positioned copy with auto-scaled canvas dimensions."""
        selected = algorithm or self._algorithm_for(model.diagram_type)
        nodes = list(model.nodes)
        if not nodes:
            return model.model_copy(update={"width": 800.0, "height": 500.0, "page_count": 1})
        positions = self._manual_positions(nodes) if selected == "manual" else self._positions(nodes, selected, minimum_distance)
        positioned = [node.model_copy(update={"position": positions[node.node_id]}) for node in nodes]
        width = max(800.0, max(item.x for item in positions.values()) + minimum_distance)
        height = max(500.0, max(item.y for item in positions.values()) + minimum_distance)
        page_count = max(1, math.ceil((width * height) / (1800.0 * 1200.0)))
        return model.model_copy(update={"nodes": positioned, "width": width, "height": height, "page_count": page_count})

    @staticmethod
    def _algorithm_for(diagram_type: DiagramType) -> str:
        """Select a layout suited to the diagram family."""
        if diagram_type in {DiagramType.WAN_TOPOLOGY, DiagramType.VPN_TOPOLOGY, DiagramType.DR_TOPOLOGY}:
            return "radial"
        if diagram_type in {DiagramType.RACK_ELEVATION, DiagramType.FLOOR_PLAN, DiagramType.CABLE_PATHWAY, DiagramType.IP_SCHEMA}:
            return "grid"
        if diagram_type == DiagramType.ROUTING_DOMAIN:
            return "hierarchical"
        return "force_directed"

    @staticmethod
    def _manual_positions(nodes: Iterable[DiagramNode]) -> dict[str, Position]:
        """Respect explicit source-provided coordinates and use a safe fallback for others."""
        result: dict[str, Position] = {}
        for index, node in enumerate(nodes):
            raw = node.metadata.get("position")
            if isinstance(raw, dict) and "x" in raw and "y" in raw:
                result[node.node_id] = Position(x=float(raw["x"]), y=float(raw["y"]))
            else:
                result[node.node_id] = Position(x=200.0 + index * 160.0, y=200.0)
        return result

    @staticmethod
    def _positions(nodes: list[DiagramNode], algorithm: str, minimum_distance: float) -> dict[str, Position]:
        """Calculate positions using hierarchical, radial, grid, or deterministic force-like placement."""
        if algorithm == "grid":
            columns = max(1, math.ceil(math.sqrt(len(nodes))))
            return {node.node_id: Position(x=200.0 + (index % columns) * minimum_distance, y=180.0 + (index // columns) * minimum_distance) for index, node in enumerate(nodes)}
        if algorithm == "radial":
            center = nodes[0].node_id
            result = {center: Position(x=600.0, y=500.0)}
            radius = max(220.0, len(nodes) * 35.0)
            others = nodes[1:]
            for index, node in enumerate(others):
                angle = 2 * math.pi * index / max(1, len(others))
                result[node.node_id] = Position(x=600.0 + radius * math.cos(angle), y=500.0 + radius * math.sin(angle))
            return result
        if algorithm == "hierarchical":
            result = {}
            for index, node in enumerate(nodes):
                role = str(node.metadata.get("role", "")).lower()
                row = 0 if role in {"core", "router", "firewall"} else 1 if role in {"distribution", "aggregation"} else 2
                same_row = sum(1 for prior in nodes[:index] if (str(prior.metadata.get("role", "")).lower() in {"core", "router", "firewall"} if row == 0 else str(prior.metadata.get("role", "")).lower() in {"distribution", "aggregation"} if row == 1 else True))
                result[node.node_id] = Position(x=180.0 + same_row * minimum_distance, y=170.0 + row * minimum_distance)
            return result
        columns = max(1, math.ceil(math.sqrt(len(nodes))))
        return {node.node_id: Position(x=180.0 + (index % columns) * minimum_distance, y=170.0 + (index // columns) * minimum_distance) for index, node in enumerate(nodes)}
