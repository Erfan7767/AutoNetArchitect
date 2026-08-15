"""Shared exporter protocol for positioned diagram models."""

from __future__ import annotations

from pathlib import Path

from ..diagram_models import DiagramModel


class BaseDiagramExporter:
    """Base class for deterministic file exporters."""

    extension: str = ""

    def export(self, model: DiagramModel, output_path: str | Path) -> int:
        """Export a diagram through a concrete exporter implementation."""
        raise TypeError("a concrete diagram exporter is required for export")

    @staticmethod
    def ensure_parent(output_path: str | Path) -> Path:
        """Create the target directory and return a Path."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
