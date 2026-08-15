"""Wireless coverage diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records


class WirelessCoverageGenerator(BaseDiagramGenerator):
    """Generate AP placement and evidence-bounded coverage markers."""

    diagram_type = DiagramType.WIRELESS_COVERAGE
    title = "Wireless Coverage Diagram"
    source_keys = ("access_points", "wireless_design", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.WIRELESS

    def build_warnings(self, *, artifacts, nodes, edges):
        """Prevent a design-only AP plot from being described as RF validated."""
        warnings = super().build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        evidence = artifacts.get("wireless_evidence", artifacts.get("survey_evidence"))
        if not evidence:
            warnings.append("PENDING: no survey-backed RF evidence; coverage is not RF validated")
        return warnings
