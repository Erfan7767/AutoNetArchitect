"""VPN topology diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType, NodeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class VPNTopologyGenerator(BaseDiagramGenerator):
    """Generate VPN endpoint nodes and explicitly recorded tunnel edges."""

    diagram_type = DiagramType.VPN_TOPOLOGY
    title = "VPN Topology Diagram"
    source_keys = ("vpn_tunnels", "vpn_design", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.VPN

    def build_warnings(self, *, artifacts, nodes, edges):
        """Warn when tunnel status is design-only rather than observed."""
        warnings = super().build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        if not artifacts.get("operational_state") and not artifacts.get("discovered_state"):
            warnings.append("PENDING: VPN operational status was not supplied; diagram shows design records only")
        return warnings
