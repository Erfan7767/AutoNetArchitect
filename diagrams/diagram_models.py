"""Pydantic v2 contracts for source-driven network diagrams."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DiagramType(str, Enum):
    """Supported diagram views."""

    PHYSICAL_TOPOLOGY = "physical_topology"
    LOGICAL_TOPOLOGY = "logical_topology"
    L3_TOPOLOGY = "l3_topology"
    L2_TOPOLOGY = "l2_topology"
    SECURITY_ZONES = "security_zones"
    WAN_TOPOLOGY = "wan_topology"
    SITE_OVERVIEW = "site_overview"
    RACK_ELEVATION = "rack_elevation"
    FLOOR_PLAN = "floor_plan"
    CABLE_PATHWAY = "cable_pathway"
    VLAN_MAP = "vlan_map"
    ROUTING_DOMAIN = "routing_domain"
    VPN_TOPOLOGY = "vpn_topology"
    DR_TOPOLOGY = "dr_topology"
    WIRELESS_COVERAGE = "wireless_coverage"
    IP_SCHEMA = "ip_schema"
    DEPENDENCY_GRAPH = "dependency_graph"


class DiagramScope(str, Enum):
    """Scope of a diagram request."""

    ENTIRE_NETWORK = "entire_network"
    PER_SITE = "per_site"
    PER_BUILDING = "per_building"
    PER_FLOOR = "per_floor"


class DetailLevel(str, Enum):
    """Amount of data rendered in a diagram."""

    OVERVIEW = "overview"
    STANDARD = "standard"
    DETAILED = "detailed"


class OutputFormat(str, Enum):
    """Supported diagram export formats."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    DRAWIO = "drawio"
    MERMAID = "mermaid"
    GRAPHVIZ = "graphviz"


class DiagramStyle(str, Enum):
    """Visual style presets."""

    DEFAULT = "default"
    PRESENTATION = "presentation"
    PRINT = "print"
    BLUEPRINT = "blueprint"


class RedactionLevel(str, Enum):
    """Diagram redaction policy."""

    NONE = "none"
    STANDARD = "standard"
    STRICT = "strict"


class NodeType(str, Enum):
    """Diagram node categories."""

    ROUTER = "router"
    SWITCH_L2 = "switch_l2"
    SWITCH_L3 = "switch_l3"
    FIREWALL = "firewall"
    WLC = "wlc"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    WORKSTATION = "workstation"
    PHONE = "phone"
    PRINTER = "printer"
    CAMERA = "camera"
    IOT_DEVICE = "iot_device"
    CLOUD = "cloud"
    INTERNET = "internet"
    VPN_CONCENTRATOR = "vpn_concentrator"
    LOAD_BALANCER = "load_balancer"
    WAN_LINK = "wan_link"
    BUILDING = "building"
    FLOOR = "floor"
    RACK = "rack"
    SITE = "site"
    SERVICE = "service"
    VLAN = "vlan"
    SUBNET = "subnet"
    UNKNOWN = "unknown"


class EdgeType(str, Enum):
    """Diagram edge categories."""

    PHYSICAL = "physical"
    LOGICAL = "logical"
    TRUNK = "trunk"
    PORT_CHANNEL = "port_channel"
    WAN = "wan"
    VPN = "vpn"
    WIRELESS = "wireless"
    DEPENDENCY = "dependency"
    ROUTING = "routing"
    SECURITY_FLOW = "security_flow"


class EdgeStyle(str, Enum):
    """Diagram line styles."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    THICK = "thick"


class GroupType(str, Enum):
    """Diagram group/container categories."""

    SITE = "site"
    BUILDING = "building"
    FLOOR = "floor"
    RACK = "rack"
    VLAN = "vlan"
    ZONE = "zone"
    AREA = "area"
    SUBNET = "subnet"
    SERVICE = "service"


class Position(BaseModel):
    """Two-dimensional position in diagram coordinate space."""

    model_config = ConfigDict(extra="forbid")

    x: float = 0.0
    y: float = 0.0


class GroupStyle(BaseModel):
    """Visual style for a diagram group."""

    model_config = ConfigDict(extra="forbid")

    fill_color: str = "#F7F9FC"
    border_color: str = "#667085"
    border_style: EdgeStyle = EdgeStyle.SOLID
    opacity: float = Field(default=0.18, ge=0.0, le=1.0)


class DiagramNode(BaseModel):
    """One source-backed node in a diagram."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    node_type: NodeType
    label: str = Field(min_length=1)
    vendor: str = ""
    model: str = ""
    icon: str = "generic/unknown"
    position: Position = Field(default_factory=Position)
    metadata: dict[str, Any] = Field(default_factory=dict)
    style_overrides: dict[str, Any] = Field(default_factory=dict)
    uncertain: bool = False
    source_artifacts: list[str] = Field(default_factory=list)


class DiagramEdge(BaseModel):
    """One source-backed relationship between two nodes."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    source_node: str = Field(min_length=1)
    target_node: str = Field(min_length=1)
    edge_type: EdgeType
    label: str = ""
    source_interface: str = ""
    target_interface: str = ""
    bandwidth: str = ""
    style: EdgeStyle = EdgeStyle.SOLID
    color: str = "#667085"
    bidirectional: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    uncertain: bool = False
    source_artifacts: list[str] = Field(default_factory=list)


class DiagramGroup(BaseModel):
    """Container for nodes with a shared site, zone, VLAN, or layout context."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(min_length=1)
    group_type: GroupType
    label: str = Field(min_length=1)
    members: list[str] = Field(default_factory=list)
    style: GroupStyle = Field(default_factory=GroupStyle)
    metadata: dict[str, Any] = Field(default_factory=dict)
    uncertain: bool = False


class LegendEntry(BaseModel):
    """One explicit legend item."""

    model_config = ConfigDict(extra="forbid")

    category: str
    label: str
    value: str
    visual: str


class LabelConfig(BaseModel):
    """Controls which source-backed fields appear on labels."""

    model_config = ConfigDict(extra="forbid")

    show_hostname: bool = True
    show_management_ip: bool = False
    show_model: bool = False
    show_role: bool = True
    show_site: bool = False
    show_building: bool = False
    show_floor: bool = False
    show_interfaces: bool = False
    show_bandwidth: bool = False
    show_vlan: bool = False
    show_ip_addresses: bool = False
    show_cable_id: bool = False
    show_uncertainty_marker: bool = True
    node_placement: str = "below"
    edge_placement: str = "center"
    font_size: int = Field(default=12, ge=6, le=32)


class DiagramModel(BaseModel):
    """Complete positioned diagram model before export."""

    model_config = ConfigDict(extra="forbid")

    diagram_type: DiagramType
    title: str
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    groups: list[DiagramGroup] = Field(default_factory=list)
    legend: list[LegendEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    width: float = Field(default=1200.0, gt=0)
    height: float = Field(default=800.0, gt=0)
    page_count: int = Field(default=1, ge=1)
    warnings: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Reject duplicate identifiers and invented dangling connections."""
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("diagram node identifiers must be unique")
        node_set = set(node_ids)
        for edge in self.edges:
            if edge.source_node not in node_set or edge.target_node not in node_set:
                raise ValueError(f"edge {edge.edge_id} references a node absent from source artifacts")
        for group in self.groups:
            unknown = [member for member in group.members if member not in node_set]
            if unknown:
                raise ValueError(f"group {group.group_id} references absent nodes: {unknown}")


class DiagramRequest(BaseModel):
    """Orchestration request for one generated diagram."""

    model_config = ConfigDict(extra="forbid")

    diagram_type: DiagramType
    project_id: str
    scope: DiagramScope = DiagramScope.ENTIRE_NETWORK
    scope_value: str | None = None
    detail_level: DetailLevel = DetailLevel.STANDARD
    output_format: OutputFormat = OutputFormat.SVG
    style: DiagramStyle = DiagramStyle.DEFAULT
    labels: LabelConfig = Field(default_factory=LabelConfig)
    redaction_level: RedactionLevel = RedactionLevel.STANDARD
    output_path: str
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    schema_version: str = "1.0"


class GeneratedDiagram(BaseModel):
    """Descriptor for an exported diagram artifact."""

    model_config = ConfigDict(extra="forbid")

    diagram_type: DiagramType
    project_id: str
    scope: DiagramScope
    detail_level: DetailLevel
    output_format: OutputFormat
    file_path: str
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_basis: list[str] = Field(default_factory=list)
    schema_version: str = "1.0"
    redaction_level: RedactionLevel
    redacted: bool = True
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    group_count: int = Field(ge=0)
    page_count: int = Field(default=1, ge=1)
    uncertain_elements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_artifacts: list[str] = Field(default_factory=list)
    disclaimer: str = "Diagram generated from supplied design artifacts only; it does not prove physical installation or operational state."
