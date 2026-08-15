"""Generator for the Layer 2 Topology Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class L2TopologyGenerator(BaseDiagramGenerator):
    """Generate Layer 2 Topology Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.L2_TOPOLOGY
    title = "Layer 2 Topology Diagram"
    source_keys = ('devices', 'equipment', 'nodes', 'mappings', 'l2_design')
    default_edge_type = EdgeType.TRUNK
