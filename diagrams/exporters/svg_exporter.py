"""Self-contained SVG exporter for editable vector diagrams."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle, NodeType


class SVGExporter(BaseDiagramExporter):
    """Render nodes, groups, edges, and legends as SVG primitives."""

    extension = "svg"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write a readable SVG using model positions only."""
        target = self.ensure_parent(output_path)
        parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{model.width:.0f}' height='{model.height:.0f}' viewBox='0 0 {model.width:.0f} {model.height:.0f}'>", "<style>.node{stroke:#344054;stroke-width:1.5}.label{font:12px Arial,sans-serif;fill:#101828}.edge-label{font:10px Arial,sans-serif;fill:#344054}.group{fill-opacity:.18;stroke-width:1.2}.warning{fill:#B54708;font:12px Arial,sans-serif}</style>"]
        for group in model.groups:
            members = [node for node in model.nodes if node.node_id in group.members]
            if not members:
                continue
            min_x = min(node.position.x for node in members) - 80
            min_y = min(node.position.y for node in members) - 65
            max_x = max(node.position.x for node in members) + 80
            max_y = max(node.position.y for node in members) + 65
            parts.append(f"<rect class='group' x='{min_x:.1f}' y='{min_y:.1f}' width='{max_x-min_x:.1f}' height='{max_y-min_y:.1f}' fill='{escape(group.style.fill_color)}' stroke='{escape(group.style.border_color)}'/>")
            parts.append(f"<text class='label' x='{min_x+8:.1f}' y='{min_y+18:.1f}'>{escape(group.label)}</text>")
        node_map = {node.node_id: node for node in model.nodes}
        for edge in model.edges:
            source = node_map[edge.source_node].position
            target_position = node_map[edge.target_node].position
            dash = " stroke-dasharray='8,5'" if edge.style == EdgeStyle.DASHED else " stroke-dasharray='3,4'" if edge.style == EdgeStyle.DOTTED else ""
            width = 3.5 if edge.style == EdgeStyle.THICK else 1.8
            parts.append(f"<line x1='{source.x:.1f}' y1='{source.y:.1f}' x2='{target_position.x:.1f}' y2='{target_position.y:.1f}' stroke='{escape(edge.color)}' stroke-width='{width}'{dash}/>")
            if edge.label:
                mid_x = (source.x + target_position.x) / 2
                mid_y = (source.y + target_position.y) / 2
                parts.append(f"<text class='edge-label' x='{mid_x:.1f}' y='{mid_y-5:.1f}' text-anchor='middle'>{escape(edge.label).replace(chr(10), ' / ')}</text>")
        for node in model.nodes:
            fill = node.style_overrides.get("fill", "#FFFFFF")
            if node.node_type == NodeType.FIREWALL:
                fill = node.style_overrides.get("fill", "#FDEAD7")
            parts.append(f"<rect class='node' x='{node.position.x-55:.1f}' y='{node.position.y-28:.1f}' width='110' height='56' rx='10' fill='{escape(str(fill))}'/>")
            parts.append(f"<text class='label' x='{node.position.x:.1f}' y='{node.position.y+4:.1f}' text-anchor='middle'>{escape(node.label).replace(chr(10), ' / ')}</text>")
        for index, item in enumerate(model.warnings):
            parts.append(f"<text class='warning' x='20' y='{model.height-20-index*16:.1f}'>{escape(item)}</text>")
        parts.append("</svg>")
        target.write_text("".join(parts), encoding="utf-8")
        return model.page_count
