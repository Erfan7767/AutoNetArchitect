"""Generator for the Security Zone Diagram."""
from __future__ import annotations

from ..diagram_models import DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator


class SecurityZoneGenerator(BaseDiagramGenerator):
    """Generate Security Zone Diagram from supplied source artifacts only."""

    diagram_type = DiagramType.SECURITY_ZONES
    title = "Security Zone Diagram"
    source_keys = ('devices', 'equipment', 'nodes', 'security_design', 'zones', 'firewall_rules')
    default_edge_type = EdgeType.SECURITY_FLOW
