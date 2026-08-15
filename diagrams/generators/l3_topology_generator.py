"""Generator for the Layer 3 Topology Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class L3TopologyGenerator(BaseDiagramGenerator):
    """Generate Layer 3 Topology Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.L3_TOPOLOGY
    title = "Layer 3 Topology Diagram"
    source_keys = ('devices', 'equipment', 'nodes', 'l3_interfaces', 'routing_design')
    default_edge_type = EdgeType.ROUTING
