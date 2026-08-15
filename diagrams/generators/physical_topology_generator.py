"""Generator for the Physical Topology Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class PhysicalTopologyGenerator(BaseDiagramGenerator):
    """Generate Physical Topology Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.PHYSICAL_TOPOLOGY
    title = "Physical Topology Diagram"
    source_keys = ('equipment', 'devices', 'nodes')
    default_edge_type = EdgeType.PHYSICAL
