"""Generator for the Logical Topology Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class LogicalTopologyGenerator(BaseDiagramGenerator):
    """Generate Logical Topology Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.LOGICAL_TOPOLOGY
    title = "Logical Topology Diagram"
    source_keys = ('devices', 'equipment', 'nodes', 'vlan_design', 'ip_design')
    default_edge_type = EdgeType.LOGICAL
