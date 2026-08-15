"""Shared source-artifact extraction for all diagram generators."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Iterable

from ..diagram_models import DiagramEdge, DiagramGroup, DiagramModel, DiagramNode, DiagramScope, DiagramType, EdgeStyle, EdgeType, GroupType, NodeType, Position
from ..icon_library import IconLibrary
from ..diagram_style_manager import DiagramStyleManager


class BaseDiagramGenerator:
    """Build bounded diagram models only from supplied records."""

    diagram_type: DiagramType
    title: str = "Network Diagram"
    source_keys: tuple[str, ...] = ()
    default_edge_type: EdgeType = EdgeType.LOGICAL

    def __init__(self, *, icon_library: IconLibrary | None = None, style_manager: DiagramStyleManager | None = None) -> None:
        """Initialize shared icon and style services."""
        self.icon_library = icon_library or IconLibrary()
        self.style_manager = style_manager or DiagramStyleManager()

    def generate(self, *, artifacts: Mapping[str, Any], scope: DiagramScope | str = DiagramScope.ENTIRE_NETWORK, scope_value: str | None = None, detail_level: str = "standard") -> DiagramModel:
        """Generate a model and mark missing or ambiguous records as uncertain."""
        nodes = self.build_nodes(artifacts=artifacts, scope=scope, scope_value=scope_value, detail_level=detail_level)
        edges = self.build_edges(artifacts=artifacts, nodes=nodes, detail_level=detail_level)
        groups = self.build_groups(nodes=nodes, artifacts=artifacts)
        warnings = self.build_warnings(artifacts=artifacts, nodes=nodes, edges=edges)
        model = DiagramModel(diagram_type=self.diagram_type, title=self.title, nodes=nodes, edges=edges, groups=groups, metadata={"source_keys": list(self.source_keys), "detail_level": detail_level, "scope": str(scope), "scope_value": scope_value or ""}, warnings=warnings)
        return model.model_copy(update={"legend": []})

    def build_nodes(self, *, artifacts: Mapping[str, Any], scope: DiagramScope | str, scope_value: str | None, detail_level: str) -> list[DiagramNode]:
        """Build device or semantic nodes from direct and domain-specific records."""
        records: list[Mapping[str, Any]] = []
        for key in self.source_keys:
            records.extend(self.records(artifacts.get(key)))
        records.extend(self.records(artifacts.get("nodes")))
        unique: dict[str, DiagramNode] = {}
        for index, record in enumerate(records):
            node = self.node_from_record(record, index=index)
            if node is None or not self.in_scope(node, scope, scope_value):
                continue
            unique[node.node_id] = node
        if not unique:
            topology = artifacts.get("topology")
            for index, record in enumerate(self.records(topology)):
                node = self.node_from_record(record, index=index)
                if node is not None and self.in_scope(node, scope, scope_value):
                    unique[node.node_id] = node
        return list(unique.values())

    def build_edges(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], detail_level: str) -> list[DiagramEdge]:
        """Build edges from explicit links, physical runs, or complete port mappings."""
        node_ids = {node.node_id for node in nodes}
        candidate_records: list[Mapping[str, Any]] = []
        for key in ("links", "connections", "cables", "cable_runs"):
            candidate_records.extend(self.records(artifacts.get(key)))
        physical = artifacts.get("physical_design")
        if isinstance(physical, Mapping):
            cabling = physical.get("cabling")
            candidate_records.extend(self.records(cabling.get("runs") if isinstance(cabling, Mapping) else None))
        candidate_records.extend(self.records(artifacts.get("mappings")))
        edges: dict[tuple[str, str, str], DiagramEdge] = {}
        for index, record in enumerate(candidate_records):
            source = self.text(record, "source_node", "source", "device", "from_device", "local_device")
            target = self.text(record, "target_node", "target", "remote_device", "to_device", "peer_device")
            if not source or not target or source not in node_ids or target not in node_ids or source == target:
                continue
            ordered = tuple(sorted((source, target)))
            key = (ordered[0], ordered[1], self.text(record, "edge_type", "type") or self.default_edge_type.value)
            edge = self.edge_from_record(record, source=source, target=target, index=index)
            edges[key] = edge
        return list(edges.values())

    def build_groups(self, *, nodes: list[DiagramNode], artifacts: Mapping[str, Any]) -> list[DiagramGroup]:
        """Group nodes using explicit source metadata only."""
        buckets: dict[tuple[GroupType, str], list[str]] = {}
        for node in nodes:
            site = str(node.metadata.get("site", "")).strip()
            building = str(node.metadata.get("building", "")).strip()
            floor = str(node.metadata.get("floor", "")).strip()
            if site:
                buckets.setdefault((GroupType.SITE, site), []).append(node.node_id)
            if building:
                buckets.setdefault((GroupType.BUILDING, building), []).append(node.node_id)
            if floor:
                buckets.setdefault((GroupType.FLOOR, floor), []).append(node.node_id)
        return [DiagramGroup(group_id=f"{kind.value}_{label}", group_type=kind, label=label, members=list(dict.fromkeys(members))) for (kind, label), members in sorted(buckets.items(), key=lambda item: (item[0][0].value, item[0][1]))]

    def build_warnings(self, *, artifacts: Mapping[str, Any], nodes: list[DiagramNode], edges: list[DiagramEdge]) -> list[str]:
        """Expose missing inputs and unresolved source data as warnings."""
        warnings: list[str] = []
        if not nodes:
            warnings.append(f"PENDING: no source records for {self.diagram_type.value}")
        if not edges and nodes:
            warnings.append("PENDING: no complete source-backed connections were supplied")
        if any(node.uncertain for node in nodes) or any(edge.uncertain for edge in edges):
            warnings.append("UNCONFIRMED: one or more elements have incomplete or ambiguous source data")
        return warnings

    def node_from_record(self, record: Mapping[str, Any], *, index: int) -> DiagramNode | None:
        """Normalize a record into a node without inventing an identifier."""
        node_id = self.text(record, "node_id", "id", "device_id", "hostname", "device", "name")
        if not node_id:
            return None
        node_type = self.node_type(record)
        vendor = self.text(record, "vendor", "manufacturer") or ""
        model = self.text(record, "model", "platform") or ""
        metadata = dict(record.get("metadata", {})) if isinstance(record.get("metadata"), Mapping) else {}
        for key in ("hostname", "role", "site", "building", "floor", "management_ip", "rack", "ru_position", "ru_height", "zone", "vlan", "subnet", "area", "asn", "status", "confidence"):
            if key in record and key not in metadata:
                metadata[key] = record[key]
        uncertain = self.is_uncertain(record, model=model)
        return DiagramNode(node_id=node_id, node_type=node_type, label=self.text(record, "label", "hostname", "name") or node_id, vendor=vendor, model=model, icon=self.icon_library.select(vendor=vendor, node_type=node_type.value), metadata=metadata, uncertain=uncertain, source_artifacts=[str(record.get("source_artifact", "design_artifacts"))])

    def edge_from_record(self, record: Mapping[str, Any], *, source: str, target: str, index: int) -> DiagramEdge:
        """Normalize a complete relationship record into a DiagramEdge."""
        edge_type_raw = self.text(record, "edge_type", "type") or self.default_edge_type.value
        try:
            edge_type = EdgeType(edge_type_raw)
        except ValueError:
            edge_type = self.default_edge_type
        style_raw = self.text(record, "style", "edge_style") or EdgeStyle.SOLID.value
        try:
            style = EdgeStyle(style_raw)
        except ValueError:
            style = EdgeStyle.SOLID
        metadata = dict(record.get("metadata", {})) if isinstance(record.get("metadata"), Mapping) else {}
        for key in ("vlan", "allowed_vlans", "native_vlan", "cable_id", "ip_addresses", "media", "status"):
            if key in record and key not in metadata:
                metadata[key] = record[key]
        uncertain = self.is_uncertain(record, model="") or not self.text(record, "source_interface", "interface", "from_interface") or not self.text(record, "target_interface", "remote_interface", "to_interface")
        return DiagramEdge(edge_id=self.text(record, "edge_id", "id", "cable_id") or f"edge_{index}", source_node=source, target_node=target, edge_type=edge_type, label=self.text(record, "label", "description", "role") or "", source_interface=self.text(record, "source_interface", "interface", "from_interface") or "", target_interface=self.text(record, "target_interface", "remote_interface", "to_interface") or "", bandwidth=self.text(record, "bandwidth", "speed", "capacity") or "", style=style, color=self.style_manager.edge_color(edge_type.value, "default"), bidirectional=bool(record.get("bidirectional", True)), metadata=metadata, uncertain=uncertain, source_artifacts=[str(record.get("source_artifact", "design_artifacts"))])

    @staticmethod
    def node_type(record: Mapping[str, Any]) -> NodeType:
        """Infer a node category only from explicit role or type words."""
        raw = str(record.get("node_type") or record.get("type") or record.get("role") or "unknown").lower().replace("-", "_").replace(" ", "_")
        aliases = {"switch": NodeType.SWITCH_L2, "l2_switch": NodeType.SWITCH_L2, "l3_switch": NodeType.SWITCH_L3, "core": NodeType.SWITCH_L3, "distribution": NodeType.SWITCH_L3, "aggregation": NodeType.SWITCH_L3, "access": NodeType.SWITCH_L2, "access_switch": NodeType.SWITCH_L2, "router": NodeType.ROUTER, "firewall": NodeType.FIREWALL, "ap": NodeType.ACCESS_POINT, "access_point": NodeType.ACCESS_POINT, "wlc": NodeType.WLC, "internet": NodeType.INTERNET, "cloud": NodeType.CLOUD, "server": NodeType.SERVER, "vpn": NodeType.VPN_CONCENTRATOR, "load_balancer": NodeType.LOAD_BALANCER, "building": NodeType.BUILDING, "rack": NodeType.RACK, "site": NodeType.SITE, "service": NodeType.SERVICE, "vlan": NodeType.VLAN, "subnet": NodeType.SUBNET}
        return aliases.get(raw, NodeType.UNKNOWN)

    @staticmethod
    def is_uncertain(record: Mapping[str, Any], *, model: str) -> bool:
        """Mark records uncertain when confidence or status says so, or essential identity is missing."""
        confidence = record.get("confidence")
        low_confidence = isinstance(confidence, (int, float)) and confidence < 0.8
        status = str(record.get("status", "")).lower()
        return low_confidence or status in {"unknown", "pending", "ambiguous", "unverified", "not_supplied"} or not model and str(record.get("node_type", record.get("type", ""))).lower() in {"device", "router", "switch", "firewall"}

    @staticmethod
    def in_scope(node: DiagramNode, scope: DiagramScope | str, scope_value: str | None) -> bool:
        """Filter nodes by explicit scope fields only."""
        selected = DiagramScope(scope)
        if selected == DiagramScope.ENTIRE_NETWORK or not scope_value:
            return True
        field = {DiagramScope.PER_SITE: "site", DiagramScope.PER_BUILDING: "building", DiagramScope.PER_FLOOR: "floor"}[selected]
        return str(node.metadata.get(field, "")) == scope_value

    @staticmethod
    def records(value: Any) -> list[Mapping[str, Any]]:
        """Normalize mappings and sequences into record mappings."""
        if isinstance(value, Mapping):
            if any(key in value for key in ("nodes", "links", "runs", "rows", "items", "devices", "rules", "records")):
                for key in ("nodes", "links", "runs", "rows", "items", "devices", "rules", "records"):
                    nested = value.get(key)
                    if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
                        return [item for item in nested if isinstance(item, Mapping)]
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [item for item in value if isinstance(item, Mapping)]
        return []

    @staticmethod
    def text(record: Mapping[str, Any], *keys: str) -> str | None:
        """Return the first non-empty scalar value from supplied keys."""
        for key in keys:
            value = record.get(key)
            if value is not None and not isinstance(value, (dict, list, tuple, set)) and str(value).strip():
                return str(value).strip()
        return None
