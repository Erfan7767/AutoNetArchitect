"""PDF exporter for printable network diagrams."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle


class PDFExporter(BaseDiagramExporter):
    """Render a positioned diagram onto one or more PDF pages."""

    extension = "pdf"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write a vector PDF with basic edges and node labels."""
        target = self.ensure_parent(output_path)
        width, height = landscape(A4)
        scale = min((width - 60) / model.width, (height - 70) / model.height)
        pdf = canvas.Canvas(str(target), pagesize=(width, height))
        node_map = {node.node_id: node for node in model.nodes}
        pdf.setTitle(model.title)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(24, height - 28, model.title)
        for edge in model.edges:
            source = node_map[edge.source_node].position
            target_position = node_map[edge.target_node].position
            pdf.setStrokeColor(edge.color or "#667085")
            pdf.setLineWidth(3 if edge.style == EdgeStyle.THICK else 1.5)
            pdf.line(30 + source.x * scale, 40 + source.y * scale, 30 + target_position.x * scale, 40 + target_position.y * scale)
        for node in model.nodes:
            x = 30 + node.position.x * scale
            y = 40 + node.position.y * scale
            pdf.setFillColor(node.style_overrides.get("fill", "#FFFFFF"))
            pdf.setStrokeColor("#344054")
            pdf.roundRect(x - 42, y - 18, 84, 36, 6, fill=1, stroke=1)
            pdf.setFillColor("#101828")
            pdf.setFont("Helvetica", 8)
            pdf.drawCentredString(x, y - 3, node.label.replace("\n", " / ")[:42])
        pdf.setFont("Helvetica", 7)
        for index, warning in enumerate(model.warnings):
            pdf.setFillColor("#B54708")
            pdf.drawString(24, 18 + index * 9, warning[:150])
        pdf.save()
        return 1
