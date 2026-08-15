"""Legend generation for icons, colors, line styles, and uncertainty."""
from __future__ import annotations

from collections import Counter

from .diagram_models import DiagramModel, LegendEntry


class LegendGenerator:
    """Build a compact legend from the elements actually present in the model."""

    def generate(self, model: DiagramModel) -> list[LegendEntry]:
        """Return legend entries without listing unused invented elements."""
        entries: list[LegendEntry] = []
        node_types = Counter(node.node_type.value for node in model.nodes)
        for value in sorted(node_types):
            entries.append(LegendEntry(category="icon", label=value, value=str(node_types[value]), visual=f"icon:{value}"))
        edge_types = Counter(edge.edge_type.value for edge in model.edges)
        for value in sorted(edge_types):
            entries.append(LegendEntry(category="line", label=value, value=str(edge_types[value]), visual=f"line:{value}"))
        if any(node.uncertain for node in model.nodes) or any(edge.uncertain for edge in model.edges):
            entries.append(LegendEntry(category="status", label="Unconfirmed source data", value="UNCONFIRMED", visual="marker:UNCONFIRMED"))
        return entries
