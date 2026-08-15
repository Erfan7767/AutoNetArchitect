"""Diagram style presets and edge/node visual conventions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .diagram_models import DiagramStyle, EdgeStyle, NodeType


class DiagramStyleManager:
    """Provide consistent presentation, print, default, and blueprint styles."""

    def __init__(self, scheme_path: str | Path | None = None) -> None:
        """Load colors from the bundled data asset when available."""
        self.scheme_path = Path(scheme_path) if scheme_path else Path(__file__).parent / "data" / "color_schemes.json"
        self.schemes = self._load()

    def style(self, selected: DiagramStyle | str) -> dict[str, Any]:
        """Return an immutable-style dictionary for the requested preset."""
        key = DiagramStyle(selected).value
        return dict(self.schemes.get(key, self.schemes.get("default", {})))

    def node_color(self, node_type: NodeType | str, selected: DiagramStyle | str) -> str:
        """Return a color for a node type."""
        config = self.style(selected)
        return str(config.get("node_colors", {}).get(NodeType(node_type).value, config.get("node_colors", {}).get("unknown", "#D0D5DD")))

    def edge_color(self, edge_type: str, selected: DiagramStyle | str) -> str:
        """Return a color for an edge type."""
        config = self.style(selected)
        return str(config.get("edge_colors", {}).get(edge_type, "#667085"))

    def edge_width(self, bandwidth: str, edge_style: EdgeStyle | str) -> float:
        """Map supplied bandwidth and line style to a readable width."""
        style = EdgeStyle(edge_style)
        if style == EdgeStyle.THICK:
            return 4.0
        value = bandwidth.lower().replace(" ", "")
        if value.startswith("25") or value.startswith("40") or value.startswith("100"):
            return 4.0
        if value.startswith("10"):
            return 2.5
        return 1.5

    @staticmethod
    def _load(path: Path | None = None) -> dict[str, Any]:
        """Load bundled color schemes with a safe default."""
        fallback = {"default": {"background": "#FFFFFF", "text": "#101828", "node_colors": {"unknown": "#D0D5DD"}, "edge_colors": {"physical": "#2E90FA", "wan": "#F04438", "vpn": "#7F56D9"}}}
        target = path or Path(__file__).parent / "data" / "color_schemes.json"
        if not target.exists():
            return fallback
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return fallback
        return value if isinstance(value, dict) else fallback
