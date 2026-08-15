"""Configurable bilingual-safe node and edge label construction."""
from __future__ import annotations

from .diagram_models import DiagramModel, LabelConfig


class LabelEngine:
    """Apply labels only from fields supplied in node and edge metadata."""

    def apply_labels(self, model: DiagramModel, config: LabelConfig) -> DiagramModel:
        """Return a copy with labels composed from source-backed metadata."""
        nodes = [node.model_copy(update={"label": self._node_label(node, config)}) for node in model.nodes]
        edges = [edge.model_copy(update={"label": self._edge_label(edge, config)}) for edge in model.edges]
        return model.model_copy(update={"nodes": nodes, "edges": edges})

    @staticmethod
    def _node_label(node, config: LabelConfig) -> str:
        """Compose a node label with hostname always retained when present."""
        metadata = node.metadata
        values: list[str] = []
        if config.show_hostname:
            values.append(str(metadata.get("hostname") or node.label))
        if config.show_management_ip and metadata.get("management_ip"):
            values.append(str(metadata["management_ip"]))
        if config.show_model and node.model:
            values.append(node.model)
        if config.show_role and metadata.get("role"):
            values.append(str(metadata["role"]))
        if config.show_site and metadata.get("site"):
            values.append(str(metadata["site"]))
        if config.show_building and metadata.get("building"):
            values.append(str(metadata["building"]))
        if config.show_floor and metadata.get("floor"):
            values.append(str(metadata["floor"]))
        label = "\n".join(dict.fromkeys(item for item in values if item)) or node.label
        if config.show_uncertainty_marker and node.uncertain:
            label = "UNCONFIRMED: " + label
        return label

    @staticmethod
    def _edge_label(edge, config: LabelConfig) -> str:
        """Compose an edge label from interfaces, bandwidth, and supported metadata."""
        values: list[str] = []
        if config.show_interfaces and (edge.source_interface or edge.target_interface):
            values.append(f"{edge.source_interface} ↔ {edge.target_interface}".strip(" ↔"))
        if config.show_bandwidth and edge.bandwidth:
            values.append(edge.bandwidth)
        if config.show_vlan and edge.metadata.get("vlan"):
            values.append(f"VLAN {edge.metadata['vlan']}")
        if config.show_ip_addresses and edge.metadata.get("ip_addresses"):
            values.append(str(edge.metadata["ip_addresses"]))
        if config.show_cable_id and edge.metadata.get("cable_id"):
            values.append(str(edge.metadata["cable_id"]))
        if edge.label:
            values.insert(0, edge.label)
        label = " | ".join(dict.fromkeys(item for item in values if item))
        return "UNCONFIRMED: " + label if edge.uncertain and config.show_uncertainty_marker and label else label
