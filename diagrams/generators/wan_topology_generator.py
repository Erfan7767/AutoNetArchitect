"""Generator for the WAN Topology Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class WANTopologyGenerator(BaseDiagramGenerator):
    """Generate WAN Topology Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.WAN_TOPOLOGY
    title = "WAN Topology Diagram"
    source_keys = ('devices', 'equipment', 'nodes', 'wan_design', 'wan_links')
    default_edge_type = EdgeType.WAN
