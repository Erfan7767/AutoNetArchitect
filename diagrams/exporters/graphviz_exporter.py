"""Graphviz DOT exporter for complex graph workflows."""
from __future__ import annotations

import re
from pathlib import Path

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle


class GraphvizExporter(BaseDiagramExporter):
    """Write directed DOT with clusters and readable attributes."""

    extension = "dot"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write DOT source without invoking an external Graphviz process."""
        target = self.ensure_parent(output_path)
        identifiers = {node.node_id: self.safe_id(node.node_id, index) for index, node in enumerate(model.nodes)}
        lines = ["digraph AutoNetArchitect {", "  rankdir=LR;", f'  label="{self.clean(model.title)}";', "  labelloc=t;"]
        for group in model.groups:
            lines.extend([f"  subgraph cluster_{self.safe_id(group.group_id, 0)} {{", f'    label="{self.clean(group.label)}";', f'    color="{group.style.border_color}";'])
            for member in group.members:
                if member in identifiers:
                    lines.append(f"    {identifiers[member]};")
            lines.append("  }")
        for node in model.nodes:
            shape = "box" if node.node_type.value not in {"cloud", "internet"} else "cloud"
            lines.append(f'  {identifiers[node.node_id]} [label="{self.clean(node.label)}", shape={shape}];')
        for edge in model.edges:
            style = "dashed" if edge.style in {EdgeStyle.DASHED, EdgeStyle.DOTTED} else "bold" if edge.style == EdgeStyle.THICK else "solid"
            label = f', label="{self.clean(edge.label)}"' if edge.label else ""
            lines.append(f'  {identifiers[edge.source_node]} -> {identifiers[edge.target_node]} [color="{edge.color}", style={style}{label}];')
        for warning in model.warnings:
            lines.append(f'  warning [label="{self.clean(warning)}", shape=note, color="#B54708"];')
        lines.append("}")
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return model.page_count

    @staticmethod
    def safe_id(value: str, index: int) -> str:
        """Return a DOT-safe identifier."""
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
        return cleaned or f"node_{index}"

    @staticmethod
    def clean(value: str) -> str:
        """Escape DOT quote and line-break characters."""
        return str(value).replace("\\\\", "/").replace('"', "'").replace("\\n", " / ")
