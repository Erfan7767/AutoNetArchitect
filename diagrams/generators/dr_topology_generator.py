"""Disaster recovery topology diagram generator."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..diagram_models import DiagramNode, DiagramType, EdgeType
from .base_generator import BaseDiagramGenerator
from .semantic_helpers import source_records, text


class DRTopologyGenerator(BaseDiagramGenerator):
    """Generate primary/DR sites and recorded replication links."""

    diagram_type = DiagramType.DR_TOPOLOGY
    title = "Disaster Recovery Topology Diagram"
    source_keys = ("dr_sites", "dr_design", "sites", "devices", "equipment", "nodes")
    default_edge_type = EdgeType.WAN

    def build_warnings(self, *, artifacts, nodes, edges):
        """Expose missing RPO/RTO or live-state evidence."""
        warnings = super().build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        dr = artifacts.get("dr_design")
        if not isinstance(dr, Mapping) or dr.get("rpo") is None or dr.get("rto") is None:
            warnings.append("PENDING: RPO/RTO targets are not fully supplied")
        if not artifacts.get("operational_state") and not artifacts.get("discovered_state"):
            warnings.append("PENDING: DR link operational state was not supplied")
        return warnings
