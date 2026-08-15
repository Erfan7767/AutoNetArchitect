"""Editable diagrams.net/draw.io XML exporter."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle


class DrawioExporter(BaseDiagramExporter):
    """Write mxGraph XML compatible with diagrams.net."""

    extension = "drawio"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write editable nodes, containers, and labeled edges."""
        target = self.ensure_parent(output_path)
        cells = ["<mxCell id='0'/>", "<mxCell id='1' parent='0'/>"]
        for group in model.groups:
            cells.append(f"<mxCell id='{escape(group.group_id)}' value='{escape(group.label)}' style='swimlane;html=1;fillColor={escape(group.style.fill_color)};strokeColor={escape(group.style.border_color)};' vertex='1' parent='1'><mxGeometry x='0' y='0' width='240' height='160' as='geometry'/></mxCell>")
        for node in model.nodes:
            parent = next((group.group_id for group in model.groups if node.node_id in group.members), "1")
            style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={escape(str(node.style_overrides.get('fill', '#FFFFFF')))};strokeColor=#344054;"
            cells.append(f"<mxCell id='{escape(node.node_id)}' value='{escape(node.label).replace(chr(10), ' / ')}' style='{style}' vertex='1' parent='{escape(parent)}'><mxGeometry x='{node.position.x-55:.1f}' y='{node.position.y-28:.1f}' width='110' height='56' as='geometry'/></mxCell>")
        for edge in model.edges:
            dash = "dashed=1;" if edge.style == EdgeStyle.DASHED else ""
            cells.append(f"<mxCell id='{escape(edge.edge_id)}' value='{escape(edge.label)}' style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;{dash}strokeColor={escape(edge.color)};' edge='1' parent='1' source='{escape(edge.source_node)}' target='{escape(edge.target_node)}'><mxGeometry relative='1' as='geometry'/></mxCell>")
        xml = "<mxfile host='AutoNetArchitect'><diagram name='" + escape(model.title) + "'><mxGraphModel><root>" + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>"
        target.write_text(xml, encoding="utf-8")
        return model.page_count
