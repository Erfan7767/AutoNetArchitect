"""Mermaid flowchart exporter for documentation embedding."""
from __future__ import annotations

import re
from pathlib import Path

from .base_exporter import BaseDiagramExporter
from ..diagram_models import DiagramModel, EdgeStyle


class MermaidExporter(BaseDiagramExporter):
    """Write Mermaid flowchart syntax with safe identifiers."""

    extension = "mmd"

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Write a left-to-right graph with groups and labeled relationships."""
        target = self.ensure_parent(output_path)
        ids = {node.node_id: self.safe_id(node.node_id, index) for index, node in enumerate(model.nodes)}
        lines = [f"%% AutoNetArchitect {model.title}", "%% UNCONFIRMED markers identify incomplete source data", "flowchart LR"]
        grouped = {member: group for group in model.groups for member in group.members}
        opened: set[str] = set()
        for node in model.nodes:
            group = grouped.get(node.node_id)
            if group and group.group_id not in opened:
                lines.append(f"    subgraph {self.safe_id(group.group_id, len(opened))}[{self.clean(group.label)}]")
                opened.add(group.group_id)
            indent = "        " if group else "    "
            lines.append(f"{indent}{ids[node.node_id]}[{self.clean(node.label)}]")
            if group and all(item.node_id not in group.members for item in model.nodes[model.nodes.index(node)+1:]):
                lines.append("    end")
        for edge in model.edges:
            connector = "-.->" if edge.style in {EdgeStyle.DASHED, EdgeStyle.DOTTED} else "==>" if edge.style == EdgeStyle.THICK else "-->"
            label = f"|{self.clean(edge.label)}|" if edge.label else ""
            lines.append(f"    {ids[edge.source_node]} {connector}{label} {ids[edge.target_node]}")
        if model.warnings:
            lines.append("    note[" + self.clean("; ".join(model.warnings)) + "]")
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return model.page_count

    @staticmethod
    def safe_id(value: str, index: int) -> str:
        """Return a Mermaid-safe identifier."""
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
        return cleaned or f"node_{index}"

    @staticmethod
    def clean(value: str) -> str:
        """Escape Mermaid delimiter characters in labels."""
        return str(value).replace("[", "(").replace("]", ")").replace("|", "/").replace('"', "'")
