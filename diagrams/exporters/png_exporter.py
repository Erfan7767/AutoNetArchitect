"""Raster PNG exporter using Pillow."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle


class PNGExporter(BaseDiagramExporter):
    """Render a diagram to PNG without relying on external graph binaries."""

    extension = "png"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write a high-resolution raster image using source positions."""
        target = self.ensure_parent(output_path)
        image = Image.new("RGB", (max(800, int(model.width)), max(500, int(model.height))), "white")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            font = ImageFont.load_default()
        node_map = {node.node_id: node for node in model.nodes}
        for edge in model.edges:
            source = node_map[edge.source_node].position
            target_position = node_map[edge.target_node].position
            fill = edge.color or "#667085"
            width = 4 if edge.style == EdgeStyle.THICK else 2
            draw.line((source.x, source.y, target_position.x, target_position.y), fill=fill, width=width)
            if edge.label:
                draw.text(((source.x + target_position.x) / 2, (source.y + target_position.y) / 2), edge.label.replace("\n", " / "), fill="#344054", font=font, anchor="mm")
        for node in model.nodes:
            box = (node.position.x - 60, node.position.y - 30, node.position.x + 60, node.position.y + 30)
            draw.rounded_rectangle(box, radius=10, fill=node.style_overrides.get("fill", "#FFFFFF"), outline="#344054", width=2)
            draw.multiline_text((node.position.x, node.position.y), node.label, fill="#101828", font=font, anchor="mm", align="center")
        image.save(target, format="PNG")
        return model.page_count
